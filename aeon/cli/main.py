"""CLI interface for Aeon Core."""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from aeon.config import Config
from aeon.kernel.orchestrator import Orchestrator
from aeon.llm.adapters.llama_cpp import LlamaCppAdapter
from aeon.llm.adapters.remote_api import RemoteAPIAdapter
from aeon.llm.interface import LLMAdapter
from aeon.memory.kv_store import InMemoryKVStore
from aeon.observability.logger import JSONLLogger


class MockLLMAdapter(LLMAdapter):
    """Simple mock LLM adapter for CLI testing."""

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """Generate mock response with a simple plan."""
        # Extract request from prompt (look for the actual request after "Generate a plan...")
        # The prompt format is: "Generate a plan to accomplish the following request:\n\n{request}\n\nReturn a JSON plan..."
        lines = prompt.split("\n")
        request = None
        for i, line in enumerate(lines):
            if "request:" in line.lower() or "following request" in line.lower():
                # Get the next non-empty line as the request
                for j in range(i + 1, len(lines)):
                    if lines[j].strip():
                        request = lines[j].strip()
                        break
                break
        
        if not request:
            # Fallback: use the last non-empty line
            request = next((line.strip() for line in reversed(lines) if line.strip()), "unknown request")
        
        # Simple plan generation
        response_text = f"""{{
    "goal": "{request}",
    "steps": [
        {{"step_id": "step1", "description": "Process request: {request}", "status": "pending"}}
    ]
}}"""
        
        return {
            "text": response_text,
            "usage": {"prompt_tokens": 10, "completion_tokens": 20},
            "model": "mock-model",
        }

    def supports_streaming(self) -> bool:
        """Return False for mock."""
        return False


def create_orchestrator(
    config: Optional[Config] = None,
    llm_type: Optional[str] = None,
    api_key: Optional[str] = None,
    api_url: Optional[str] = None,
    model: Optional[str] = None,
    ttl: Optional[int] = None,
    log_file: Optional[Path] = None,
) -> Orchestrator:
    """
    Create an orchestrator instance.

    Args:
        config: Config instance (optional, will create one if not provided)
        llm_type: Type of LLM adapter (overrides config)
        api_key: API key for remote adapter (overrides config)
        api_url: API URL for adapter (overrides config)
        model: Model identifier (overrides config)
        ttl: Time-to-live in cycles (overrides config)
        log_file: Path to JSONL log file (overrides config)

    Returns:
        Configured Orchestrator instance
    """
    # Load config if not provided
    if config is None:
        config = Config()

    # Use command-line args if provided, otherwise use config
    llm_type = llm_type or config.get_llm_type()
    api_url = api_url or config.get_llm_url()
    model = model or config.get_llm_model()
    api_key = api_key or config.get_llm_api_key()
    ttl = ttl if ttl is not None else config.get_ttl()
    log_file = log_file or (Path(config.get_log_file()) if config.get_log_file() else None)

    # Create LLM adapter
    if llm_type == "mock":
        llm = MockLLMAdapter()
    elif llm_type == "llama-cpp":
        # Default to localhost:8000 if no URL specified
        api_url = api_url or "http://localhost:8000/v1/chat/completions"
        llm = LlamaCppAdapter(api_url=api_url, model=model)
    elif llm_type == "remote":
        llm = RemoteAPIAdapter(api_key=api_key, api_url=api_url, model=model)
    else:
        raise ValueError(f"Unknown LLM type: {llm_type}. Use 'mock', 'llama-cpp', or 'remote'")

    # Create memory
    memory = InMemoryKVStore()

    # Create logger if log file specified
    logger = None
    if log_file:
        logger = JSONLLogger(file_path=log_file)

    # Create orchestrator
    return Orchestrator(llm=llm, memory=memory, logger=logger, ttl=ttl)


def cmd_execute(args: argparse.Namespace, config: Config) -> int:
    """
    Execute a request: generate plan and run it.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        orchestrator = create_orchestrator(
            config=config,
            llm_type=args.llm,
            api_key=args.api_key,
            api_url=args.api_url,
            model=args.model,
            ttl=args.ttl,
            log_file=Path(args.log) if args.log else None,
        )

        print(f"Executing request: {args.request}")
        
        # Generate plan first to capture the LLM response
        print("\nGenerating plan...")
        plan = orchestrator.generate_plan(args.request)
        
        # Now execute the plan
        print("Executing plan...")
        result = orchestrator.execute(args.request, plan=plan)

        # Get the full state to access LLM outputs and tool history
        state = orchestrator.get_state()

        print(f"\nStatus: {result['status']}")
        print(f"TTL remaining: {result['ttl_remaining']}")

        # Display multi-pass execution information if available (Sprint 2)
        if 'execution_history' in result:
            history = result['execution_history']
            print(f"\n{'='*60}")
            print("Multi-Pass Execution Summary")
            print(f"{'='*60}")
            print(f"Execution ID: {history.get('execution_id', 'N/A')}")
            stats = history.get('overall_statistics', {})
            print(f"Total Passes: {stats.get('total_passes', 0)}")
            print(f"Total Refinements: {stats.get('total_refinements', 0)}")
            print(f"Convergence Achieved: {stats.get('convergence_achieved', False)}")
            print(f"Total Time: {stats.get('total_time', 0):.2f}s")
            
            # Display pass-by-pass information
            passes = history.get('passes', [])
            if passes:
                print(f"\nPass Details:")
                for pass_data in passes:
                    pass_num = pass_data.get('pass_number', 0)
                    phase = pass_data.get('phase', 'N/A')
                    duration = pass_data.get('timing_information', {}).get('duration', 0)
                    ttl_rem = pass_data.get('ttl_remaining', 0)
                    refinements = len(pass_data.get('refinement_changes', []))
                    
                    print(f"  Pass {pass_num} (Phase {phase}):")
                    print(f"    Duration: {duration:.2f}s")
                    print(f"    TTL Remaining: {ttl_rem}")
                    if refinements > 0:
                        print(f"    Refinements: {refinements}")
                    
                    # Show convergence assessment if available
                    eval_results = pass_data.get('evaluation_results', {})
                    if 'convergence' in eval_results:
                        conv = eval_results['convergence']
                        if isinstance(conv, dict):
                            print(f"    Converged: {conv.get('converged', False)}")
                            if 'completeness_score' in conv:
                                print(f"    Completeness: {conv.get('completeness_score', 0):.2f}")
                            if 'coherence_score' in conv:
                                print(f"    Coherence: {conv.get('coherence_score', 0):.2f}")
                    
                    # Show validation issues if available
                    if 'validation' in eval_results:
                        val = eval_results['validation']
                        if isinstance(val, dict):
                            issues = val.get('issues', [])
                            if issues:
                                print(f"    Validation Issues: {len(issues)}")
                                severity = val.get('overall_severity', 'N/A')
                                print(f"    Overall Severity: {severity}")

        if args.json:
            # Include full state in JSON output
            full_result = {
                **result,
                "state": {
                    "llm_outputs": state.llm_outputs if state else [],
                    "tool_history": state.tool_history if state else [],
                    "supervisor_actions": state.supervisor_actions if state else [],
                } if state else {},
            }
            print("\nResult (JSON):")
            print(json.dumps(full_result, indent=2, default=str))
        else:
            print(f"\nPlan:")
            # Preserve Plan object identity (T124) - use state.plan if available
            if state and state.plan:
                plan_obj = state.plan
            else:
                # Fallback to result plan dict
                plan_dict = result.get("plan", {})
                from aeon.plan.models import Plan
                try:
                    plan_obj = Plan(**plan_dict)
                except Exception:
                    plan_obj = None
            
            if plan_obj:
                print(f"  Goal: {plan_obj.goal}")
                print(f"  Steps: {len(plan_obj.steps)}")
                
                # Get execution modes from state if available (T119)
                execution_modes = getattr(state, 'execution_modes', {}) if state else {}
                
                for i, step in enumerate(plan_obj.steps, 1):
                    status = step.status.value if hasattr(step.status, 'value') else str(step.status)
                    desc = step.description
                    
                    # Display execution mode (T119)
                    execution_mode = execution_modes.get(step.step_id, "unknown")
                    mode_display = f"[{execution_mode}]" if execution_mode != "unknown" else ""
                    
                    # Display warnings for missing/invalid tools (T120)
                    warnings = []
                    if step.errors:
                        warnings.append(f"⚠️  Errors: {', '.join(step.errors)}")
                    if step.tool and execution_mode == "fallback":
                        warnings.append(f"⚠️  Tool '{step.tool}' not found, using fallback")
                    
                    # Display repaired steps (T121)
                    repaired_indicator = ""
                    if step.tool and execution_mode == "tool" and step.errors is None:
                        # Check if this was repaired (no errors but had tool)
                        repaired_indicator = " (repaired)" if hasattr(step, '_was_repaired') else ""
                    
                    # Display fallback steps (T122)
                    fallback_indicator = ""
                    if execution_mode == "fallback":
                        fallback_indicator = " (fallback reasoning)"
                    
                    step_line = f"    {i}. [{status}]{mode_display} {desc}"
                    if repaired_indicator:
                        step_line += repaired_indicator
                    if fallback_indicator:
                        step_line += fallback_indicator
                    print(step_line)
                    
                    if warnings:
                        for warning in warnings:
                            print(f"      {warning}")
                    
                    # Show final step outputs regardless of execution path (T123)
                    if state and state.memory:
                        memory_key = f"step_{step.step_id}_result"
                        step_result = state.memory.read(memory_key)
                        if step_result:
                            print(f"      Result: {step_result}")
            else:
                # Fallback to dict display if Plan object not available
                plan_dict = result.get("plan", {})
                print(f"  Goal: {plan_dict.get('goal', 'N/A')}")
                print(f"  Steps: {len(plan_dict.get('steps', []))}")
                for i, step in enumerate(plan_dict.get("steps", []), 1):
                    status = step.get("status", "unknown")
                    desc = step.get("description", "N/A")
                    print(f"    {i}. [{status}] {desc}")
            
            # Show LLM outputs
            if state and state.llm_outputs:
                print(f"\nLLM Outputs ({len(state.llm_outputs)} cycles):")
                for i, output in enumerate(state.llm_outputs, 1):
                    text = output.get("text", "")
                    if text:
                        # Show first 200 chars of each output
                        preview = text[:200] + "..." if len(text) > 200 else text
                        print(f"  Cycle {i}: {preview}")
            
            # Show tool results
            if state and state.tool_history:
                print(f"\nTool Calls ({len(state.tool_history)}):")
                for i, tool_call in enumerate(state.tool_history, 1):
                    tool_name = tool_call.get("tool_name", "unknown")
                    result = tool_call.get("result")
                    error = tool_call.get("error")
                    if result:
                        print(f"  {i}. {tool_name}: {result}")
                    elif error:
                        print(f"  {i}. {tool_name}: ERROR - {error}")
            
            # Show the generated plan (this is what the LLM produced)
            # Preserve Plan object identity (T124)
            if plan_obj:
                print(f"\n{'='*60}")
                print("Generated Plan (from LLM):")
                print(f"{'='*60}")
                print(json.dumps(plan_obj.model_dump(), indent=2))
            else:
                print(f"\n{'='*60}")
                print("Generated Plan (from LLM):")
                print(f"{'='*60}")
                plan_dict = result.get("plan", {})
                print(json.dumps(plan_dict, indent=2))
            
            # Note about step execution
            if state and not state.llm_outputs:
                print(f"\n{'='*60}")
                print("Note:")
                print(f"{'='*60}")
                print("Step execution completed, but no LLM reasoning was performed during steps.")
                print("In the current implementation, steps are marked complete without LLM calls.")
                print("The plan structure above shows what the LLM generated during plan creation.")

        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_plan(args: argparse.Namespace, config: Config) -> int:
    """
    Generate a plan from a natural language request.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        orchestrator = create_orchestrator(
            config=config,
            llm_type=args.llm,
            api_key=args.api_key,
            api_url=args.api_url,
            model=args.model,
            ttl=args.ttl,
        )

        print(f"Generating plan for: {args.request}")
        plan = orchestrator.generate_plan(args.request)

        if args.json:
            print("\nPlan (JSON):")
            print(json.dumps(plan.model_dump(), indent=2))
        else:
            print(f"\nGoal: {plan.goal}")
            print(f"Steps: {len(plan.steps)}")
            for i, step in enumerate(plan.steps, 1):
                print(f"  {i}. [{step.status}] {step.description}")

        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Aeon Core - Minimal LLM orchestration kernel",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Global options
    parser.add_argument(
        "--llm",
        choices=["mock", "llama-cpp", "remote"],
        default=None,
        help="LLM adapter type (overrides config file, default from config or llama-cpp)",
    )
    parser.add_argument("--api-key", help="API key for remote LLM adapter (overrides config)")
    parser.add_argument("--api-url", help="API URL for LLM adapter (overrides config)")
    parser.add_argument("--model", help="Model identifier (overrides config)")
    parser.add_argument("--ttl", type=int, help="Time-to-live in cycles (overrides config)")
    parser.add_argument("--log", help="Path to JSONL log file (overrides config)")
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to config file (default: .aeon.yaml in current dir, ~/.aeon.yaml, or ~/.config/aeon/config.yaml)",
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Execute command
    execute_parser = subparsers.add_parser("execute", help="Execute a request (generate plan and run it)")
    execute_parser.add_argument("request", help="Natural language request")
    execute_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # Plan command
    plan_parser = subparsers.add_parser("plan", help="Generate a plan from a request")
    plan_parser.add_argument("request", help="Natural language request")
    plan_parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Load config if path specified
    if args.config:
        config = Config(config_path=args.config)
    else:
        config = Config()

    # Route to command handler
    if args.command == "execute":
        return cmd_execute(args, config)
    elif args.command == "plan":
        return cmd_plan(args, config)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())

