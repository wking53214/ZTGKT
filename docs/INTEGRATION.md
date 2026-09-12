# Integration

## Position in UGPIS-Ω

ZTGKT is stage one of an eleven-stage pipeline. The ordering below is
reproduced from the archive's own pipeline diagram.

```
Inbound Request
    |
    v
ZTGKT     Validation Layer                 <-- this repository
    |
    v
ECP       Secure Data Ingestion            cryptographic intake, provenance
    |
    v
HTTP      Content Sanitization             content integrity filtering
    |
    v
CITADEL   Quality Routing                  profile routing, telemetry loop
    |
    v
DIT       Secure Transaction Processing    deterministic integrity
    |
    v
OBSERVE   Trajectory & Risk Analysis       early-warning platform
    |
    v
FORTRESS  Predictive State Control         Lyapunov energy, hysteresis
    |
    v
URE       Resilience Diagnostics           regime classification
    |
    v
EDDP      Evaluation / Rendering / Dispatch
    |
    v
GSA       Governance Enforcement
```

Being first is the point. Everything downstream operates on text that has
already passed the gate, so no later stage needs its own first-person or
hedging checks, and a defect in the gate is a defect in every stage's input.

## Component fingerprint

The archive records identifying signatures for each component, used to
classify a code fragment back to its system of origin. ZTGKT's:

```
Fingerprint:
  ContentValidationPipeline
  _guarded_generator()
  validated_content
  execution_gateway

Classification:
  Generation containment layer

Purpose:
  Controls downstream text generation execution.
```

All four identifiers are preserved in this package.

## Wiring pattern

The controller holds the gate privately and exposes only a guarded generator.
No other component receives the raw model callable.

```python
class UGPISOmegaController:
    def __init__(self, base_text_generator, ...):
        self._ztgkt_pipeline = ContentValidationPipeline(
            execution_gateway=base_text_generator
        )
        self.citadel = ContentQualityRouter(text_generator=self._guarded_generator, ...)

    async def _guarded_generator(self, prompt: str) -> str:
        result = await self._ztgkt_pipeline.execute(prompt)
        return result["validated_content"]
```

Reproduce this shape in any host. The property that matters is that
`base_text_generator` is captured by the gate and never handed on.

`GateResult` supports `result["validated_content"]` as well as attribute
access, so this archived call site works unchanged against this package.

## Using it standalone

Nothing here depends on the rest of the stack. The package has no runtime
dependencies. The only contract is the generator signature:

```python
Callable[[str], Awaitable[str]]
```

Anything satisfying it works: an SDK call, an HTTP client, a local model, a
stub in a test.
