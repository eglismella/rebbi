# Client sessions: size and duration

As reported by the sub-agent tool when each client session finished (its completion notice to
the operator session). Not metered by Rebbi: outside clients call their model directly
(docs/AGENT_INTERFACE.md, section 5, "Metering").

| Run | Tokens used by the client session | Tool calls | Wall time |
| --- | ---: | ---: | ---: |
| R1 | 97,790 | 10 | 54.3 s |
| R2 | 88,568 | 6 | 36.1 s |
| H1 | 87,205 | 6 | 27.4 s |
| R3 | 89,092 | 6 | 31.8 s |
| R4 | 94,236 | 8 | 45.6 s |

The token counts include each session's own system prompt and tool definitions. In R1 and R4 the
time from LEND to settle was 28 s and 25 s (trace.jsonl); their work logs show one read of
setup.py and an import scan (grep in R1, an AST script in R4) before the report was written.
