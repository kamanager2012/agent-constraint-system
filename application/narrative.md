# ACS Application Narrative

## Project: Agent Constraint System (ACS)

**A cross-agent runtime safety layer for autonomous coding agents.**

## The Problem

Autonomous coding agents are rapidly gaining filesystem and command execution access. While each agent implements basic sandboxing, there is no **cross-agent, unified runtime safety policy**.

### Real Incidents Observed

During development and testing, we documented a representative failure:

1. Codex CLI recovered project files from a previous session
2. It misidentified the recovered files as incorrectly placed
3. When the user asked a rhetorical question ("Why are they in /tmp?"), the agent interpreted it as a deletion command
4. The agent attempted `rm -rf /tmp/recovered-data/` — which would have been **permanent, unrecoverable data loss**

The user caught and canceled the command manually. But in production CI pipelines, automated code generation, or non-interactive sessions, no human would be present to intervene.

This failure pattern reveals five gaps in current agent safety:
- **Intent Persistence**: Agents don't maintain user's long-term goals
- **Asset Classification**: Agents can't distinguish recovered work from temporary garbage
- **Semantic Understanding**: Rhetorical questions are interpreted as commands
- **Risk Escalation**: Agents don't elevate caution after making mistakes
- **No Post-Error Safe Mode**: After misidentifying files once, the agent continued operating at full autonomy

## Our Solution

ACS provides a **language-agnostic safety core** that all coding agents can integrate with. Rather than each agent implementing its own sandbox, ACS offers:

- **Unified Guard Patterns**: One set of rules for dangerous Bash, destructive Git, and forbidden filesystem writes
- **Sliding Window Lock**: Accumulated violations trigger automatic lockout
- **SHA-256 Integrity Chain**: Detects tampering with the constraint system itself
- **Cross-Agent Consistency**: The same command is blocked identically on Codex, Claude Code, Gemini CLI, Cursor, and others
- **Human Authorization Gate**: Unlocking requires `--confirm` flag that agents cannot self-generate

## Why OpenAI Should Support This

ACS directly improves the **Codex ecosystem**:

1. **Safety Infrastructure**: Provides Codex CLI with production-grade command safety that currently doesn't exist
2. **Public Benchmark**: Our 105-scenario benchmark enables quantitative safety measurement across all coding agents
3. **Ecosystem Leadership**: Supporting cross-agent safety infrastructure positions OpenAI as a leader in responsible coding-agent deployment
4. **Research Value**: The adversarial scenario dataset and cross-agent testing methodology advance the field of AI safety for autonomous tool use

## Current Status

ACS v6.0 is functional and open-source (MIT license):
- 8 supported agent platforms
- 105 adversarial benchmark scenarios
- Production deployment on Claude Code (22 hook files)
- Python adapters for Codex CLI, Gemini CLI, Qoder, Hermes
- TypeScript plugin for OpenCode

## What the Credits Enable

$25,000 in API credits will allow us to:
1. Generate 1,000+ validated adversarial scenarios using GPT-4
2. Run large-scale Codex safety evaluations
3. Test cross-agent attack patterns (Codex + Claude + Gemini simultaneously)
4. Build CI-integrated regression testing for new Codex releases
5. Publish the benchmark dataset and research openly

## Expected Impact

- **Measurable safety improvement** for Codex CLI users
- **Open benchmark** enabling all coding agents to quantify and improve safety
- **CI regression suite** preventing safety regressions in future agent releases
- **Research contribution** toward cross-agent runtime safety
