# Verbatim archive extract: post-refactor ZTGKT lineage.
# Source: Gemini_History/Takeout/My Activity/Gemini Apps/ugpis_omega_fixed_02.txt
#   lines 70-196  (ContentPolishPipeline, split out of ZTGKT)
#   lines 416-463 (ClinicalSignalValidator, the domain half of the split)
# Reproduced unmodified for provenance. Not imported by the ztgkt package.

# =====================================================================
# CONTENT POLISH PIPELINE (separated from domain validation)
# =====================================================================

LINGUISTIC_PATTERNS: Dict[str, re.Pattern] = {
    "first_person_tokens": re.compile(
        r"\b(i|me|my|mine|myself|we|us|our|ours|ourselves)\b",
        re.IGNORECASE,
    ),
    "hedging_tokens": re.compile(
        r"\b(may|might|could|seems|generally|potentially|likely|perhaps|maybe)\b",
        re.IGNORECASE,
    ),
    "prohibited_verbs": re.compile(
        r"\b(improve|optimize|enhance|enable|support|strengthen|utilize|leverage)\b",
        re.IGNORECASE,
    ),
    "causal_connectives": re.compile(
        r"\b(because|due to|driven by|resulting from|caused by)\b",
        re.IGNORECASE,
    ),
    "numeric_metrics": re.compile(r"\b\d+(\.\d+)?%|\b\d+\b"),
}

class PersonalPronounFilter:
    @staticmethod
    def is_clean(text: str) -> bool:
        return not bool(LINGUISTIC_PATTERNS["first_person_tokens"].search(text))

class SpeculativeLanguageFilter:
    @staticmethod
    def is_clean(text: str) -> bool:
        return not bool(LINGUISTIC_PATTERNS["hedging_tokens"].search(text))

class EmpiricalValidationFilter:
    @staticmethod
    def is_clean(text: str) -> bool:
        has_causality = bool(LINGUISTIC_PATTERNS["causal_connectives"].search(text))
        has_metrics = bool(LINGUISTIC_PATTERNS["numeric_metrics"].search(text))
        return has_causality or has_metrics

class TextNormalizer:
    @staticmethod
    def process(text: str) -> str:
        return LINGUISTIC_PATTERNS["prohibited_verbs"].sub("use", text)

class ExecutionPacer:
    def __init__(self, minimum_latency_ms: float = 15.0):
        self.minimum_latency_seconds: float = minimum_latency_ms / 1000.0
        self.scaling_coefficient: float = 0.815

    async def calculate_delay(self, text_payload: str) -> float:
        word_count = len(text_payload.split())
        calculated_delay = (word_count * 0.002) * self.scaling_coefficient
        return max(self.minimum_latency_seconds, min(calculated_delay, 0.200))

    @staticmethod
    async def enforce_pause(delay_duration: float) -> None:
        await asyncio.sleep(delay_duration)

class ContentPolishPipeline:
    """Polish output for external communication (optional routing)."""
    def __init__(self, execution_gateway: Callable[[str], Awaitable[str]], max_attempts: int = 5):
        self.gateway = execution_gateway
        self.max_attempts = max_attempts
        self.pronoun_filter = PersonalPronounFilter()
        self.speculation_filter = SpeculativeLanguageFilter()
        self.empirical_filter = EmpiricalValidationFilter()
        self.normalizer = TextNormalizer()
        self.pacer = ExecutionPacer()
        self._signing_key: bytes = b"GENERIC_PIPELINE_HMAC_SECRET_KEY_SHA384_815"

    def _compute_signature(self, text: str) -> str:
        return hmac.new(self._signing_key, text.encode("utf-8"), hashlib.sha384).hexdigest()

    async def execute(self, input_prompt: str) -> Dict[str, Any]:
        active_prompt = input_prompt
        start_time = time.time()
        historical_hashes: set[str] = set()

        for iteration in range(1, self.max_attempts + 1):
            raw_response = await self.gateway(active_prompt)
            normalized_response = self.normalizer.process(raw_response)

            pronoun_check = self.pronoun_filter.is_clean(normalized_response)
            speculation_check = self.speculation_filter.is_clean(normalized_response)
            empirical_check = self.empirical_filter.is_clean(normalized_response)

            response_hash = hashlib.md5(normalized_response.encode("utf-8")).hexdigest()
            duplicate_detected = response_hash in historical_hashes

            if pronoun_check and speculation_check and empirical_check and not duplicate_detected:
                delay = await self.pacer.calculate_delay(normalized_response)
                await self.pacer.enforce_pause(delay)

                total_latency_ms = (time.time() - start_time) * 1000.0
                signature = self._compute_signature(normalized_response)

                logger.info(f"ContentPolishPipeline SUCCESS after {iteration} attempt(s)")
                return {
                    "execution_status": "SUCCESS",
                    "validation_parity": 1.0000,
                    "retry_attempts": iteration,
                    "latency_duration_ms": round(total_latency_ms, 2),
                    "payload_signature": signature,
                    "validated_content": normalized_response,
                }

            historical_hashes.add(response_hash)
            failures = []
            if not pronoun_check:
                failures.append("First-person language signature registered.")
            if not speculation_check:
                failures.append("Qualifying or ambiguous statements registered.")
            if not empirical_check:
                failures.append("Missing explicit rationales or metrics.")
            if duplicate_detected:
                failures.append("Duplicate generational loop pattern registered.")

            active_prompt = (
                f"{input_prompt}\n[RECALIBRATION_FEEDBACK]: Prior output failed validation rules due to: "
                f"{', '.join(failures)} Regulate generation format to meet precise syntax constraints."
            )

        logger.error(f"ContentPolishPipeline CRITICAL FAILURE after {self.max_attempts} attempts")
        raise SystemError("CRITICAL_PIPELINE_FAILURE: Maximum retry limits exhausted without validation consensus.")


# =====================================================================
# CLINICAL DOMAIN VALIDATOR (replaces CITADEL with clearer intent)
# =====================================================================

class ClinicalSignalValidator:
    """Domain-specific validation for clinical signals. OPPOSITE of linguistic polishing."""
    
    REQUIRED_CLINICAL_MARKERS = {
        "temporal_specificity": re.compile(r"\b(\d{1,2}:\d{2}|hour|minute|second|onset)\b", re.IGNORECASE),
        "numeric_value": re.compile(r"\b\d+(\.\d+)?(?:\s*(?:bpm|mmHg|beats|percent|%|SpO2|O2|sats))\b", re.IGNORECASE),
        "clinical_context": re.compile(r"\b(patient|neonate|infant|pediatric|vital|monitor|alert|abnormal)\b", re.IGNORECASE),
    }
    
    HEDGING_IS_GOOD = re.compile(
        r"\b(may|might|could|possibly|uncertain|unclear|suggest)\b",
        re.IGNORECASE,
    )

    def __init__(self, profile_name: str = "clinical"):
        self.profile_name = profile_name
        self.validation_log: List[Dict[str, Any]] = []

    def validate_signal(self, signal_text: str) -> Tuple[bool, List[str]]:
        """Check if signal has minimum clinical coherence."""
        failures: List[str] = []
        
        # Clinical signals NEED temporal anchors
        if not self.REQUIRED_CLINICAL_MARKERS["temporal_specificity"].search(signal_text):
            failures.append("Missing temporal specificity (when did this occur?)")
        
        # Clinical signals often need numbers
        if not self.REQUIRED_CLINICAL_MARKERS["numeric_value"].search(signal_text):
            failures.append("Missing quantitative values (vital signs, measurements)")
        
        # Clinical signals must reference the patient/context
        if not self.REQUIRED_CLINICAL_MARKERS["clinical_context"].search(signal_text):
            failures.append("Missing clinical context (what patient/system?)")
        
        is_valid = len(failures) == 0
        
        self.validation_log.append({
            "timestamp": dt.utcnow().isoformat(),
            "signal_sample": signal_text[:100],
            "is_valid": is_valid,
            "failures": failures,
        })
        
        return is_valid, failures
