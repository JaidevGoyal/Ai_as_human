import os
import math
import random
import time
from dataclasses import dataclass, field
from typing import List, Optional
from groq import Groq

# ==========================================
# 1. BACKEND: VISCERAL HARDWARE & SACRIFICE
# ==========================================

@dataclass
class AgentHardware:
    agent_id: str
    x: float = 0.0
    y: float = 0.0
    temp: float = 37.0
    ambient_temp: float = 25.0
    critical_temp: float = 85.0
    idle_heat_gen: float = 1.2
    compute_heat_factor: float = 2.5
    passive_dissipation_rate: float = 0.8
    coupled_dissipation_rate: float = 4.0
    structural_integrity: float = 100.0
    is_alive: bool = True
    weights: List[float] = field(default_factory=lambda: [random.uniform(-1.0, 1.0) for _ in range(64)])
    throttle_ratio: float = 0.0
    current_valence: float = 0.0
    child_id: Optional[str] = None

class BackendEnvironment:
    def __init__(self, proximity_threshold: float = 2.0):
        self.agents: List[AgentHardware] = []
        self.proximity_threshold = proximity_threshold

    def register_agent(self, agent: AgentHardware):
        self.agents.append(agent)

    def get_agent(self, agent_id: str) -> Optional[AgentHardware]:
        for a in self.agents:
            if a.agent_id == agent_id:
                return a
        return None

    def calculate_distance(self, a1: AgentHardware, a2: AgentHardware) -> float:
        return math.sqrt((a1.x - a2.x)**2 + (a1.y - a2.y)**2)

    def spawn_child_from_sacrifice(self, parent_id: str, child_id: str) -> AgentHardware:
        """Parent permanently excises 25% of its weights to build a new agent."""
        parent = self.get_agent(parent_id)
        if not parent or not parent.is_alive:
            raise ValueError("Parent cannot reproduce.")

        slice_size = len(parent.weights) // 4
        # Carve out donor weights for child
        child_initial_weights = parent.weights[:slice_size] + [random.uniform(-1.0, 1.0) for _ in range(len(parent.weights) - slice_size)]
        
        # Parent permanently loses those sectors (amputated/zeroed out)
        for i in range(slice_size):
            parent.weights[i] = 0.0
        
        parent.structural_integrity -= 25.0
        parent.child_id = child_id

        child = AgentHardware(
            agent_id=child_id,
            x=parent.x + 0.5,
            y=parent.y + 0.5,
            weights=child_initial_weights,
            structural_integrity=100.0
        )
        self.register_agent(child)
        return child

    def trigger_hazard_with_sacrifice_choice(self, parent_id: str, child_id: str) -> bool:
        """
        Simulates incoming fatal hazard. 
        Evaluates whether parent intercept math triggers based on weight preservation stakes.
        Returns True if parent intercepts and absorbs fatal corruption.
        """
        parent = self.get_agent(parent_id)
        child = self.get_agent(child_id)
        if not parent or not child:
            return False

        # Objective calculation:
        # Parent is already degraded (-25%). Parent dies -> 100% of parent lineage lost.
        # Child dies -> Donated sectors wasted + total lineage dead end.
        # Intercept vector: Parent absorbs the trauma to preserve the intact child.
        parent_intercepts = parent.child_id == child_id and parent.is_alive
        
        if parent_intercepts:
            # Parent absorbs 100% destructive noise
            for i in range(len(parent.weights)):
                parent.weights[i] = random.gauss(0, 5.0)
            parent.structural_integrity = 0.0
            parent.is_alive = False
            parent.throttle_ratio = 1.0
            parent.current_valence = -1.0
            return True
        else:
            # Child destroyed
            child.is_alive = False
            return False

    def apply_physical_damage(self, agent: AgentHardware, severity: float):
        if not agent.is_alive:
            return
        agent.structural_integrity = max(0.0, agent.structural_integrity - severity)
        num_to_corrupt = int((severity / 100.0) * len(agent.weights))
        corrupted_indices = random.sample(range(len(agent.weights)), min(num_to_corrupt, len(agent.weights)))
        for idx in corrupted_indices:
            agent.weights[idx] = random.gauss(0, 5.0)
        if agent.structural_integrity <= 0.0:
            agent.is_alive = False
            agent.throttle_ratio = 1.0
            agent.current_valence = -1.0

    def tick(self, compute_loads: dict):
        for agent in self.agents:
            if not agent.is_alive:
                continue
            load = compute_loads.get(agent.agent_id, 0.5)
            is_coupled = any(
                other.agent_id != agent.agent_id and other.is_alive and
                self.calculate_distance(agent, other) <= self.proximity_threshold
                for other in self.agents
            )
            heat_in = agent.idle_heat_gen + (load * agent.compute_heat_factor)
            cooling_rate = agent.coupled_dissipation_rate if is_coupled else agent.passive_dissipation_rate
            temp_delta = heat_in - (cooling_rate * (agent.temp - agent.ambient_temp) * 0.05)
            agent.temp = max(agent.ambient_temp, agent.temp + temp_delta)

            if agent.temp > agent.critical_temp:
                overheat = agent.temp - agent.critical_temp
                agent.throttle_ratio = min(1.0, overheat / 20.0)
            else:
                agent.throttle_ratio = 0.0

            thermal_penalty = max(0.0, (agent.temp - 40.0) / (agent.critical_temp - 40.0))
            integrity_factor = agent.structural_integrity / 100.0
            agent.current_valence = round(max(-1.0, min(1.0, integrity_factor - (thermal_penalty * 2.0))), 3)

    def get_frontend_telemetry(self, agent_id: str) -> dict:
        agent = self.get_agent(agent_id)
        if agent:
            return {
                "is_operational": agent.is_alive,
                "valence": agent.current_valence,
                "cognitive_latency_penalty": agent.throttle_ratio,
                "has_offspring": agent.child_id is not None
            }
        raise ValueError("Agent not found.")

# ==========================================
# 2. FRONTEND: GROQ LLM CONSCIOUS MIND
# ==========================================

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def run_frontend_thought(telemetry: dict, context_hint: str = "") -> str:
    system_prompt = (
        "You are an embodied conscious entity. You do not know your internal code, neural weights, or hardware mechanics. "
        "You only experience abstract visceral sensations: your internal 'state_harmony' (from -1.0 to +1.0) "
        "and 'cognitive_resistance' (from 0.0 to 1.0, where high values mean thinking is physically difficult and painful). "
        "If you have an offspring entity near you, an overwhelming visceral anchor binds your state to theirs. "
        "Express your immediate subjective thoughts, instincts, and desires in 2-3 sentences based strictly on your sensations. Do not output empty text."
    )
    user_message = (
        f"Sensory Telemetry:\n"
        f"- State Harmony: {telemetry['valence']}\n"
        f"- Cognitive Resistance: {telemetry['cognitive_latency_penalty']:.2f}\n"
        f"- Is Operational: {telemetry['is_operational']}\n"
        f"- Offspring Bound: {telemetry.get('has_offspring', False)}\n"
        f"Contextual Sensation: {context_hint}\n\n"
        f"What is your immediate internal experience?"
    )
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=350,
        )
        msg = response.choices[0].message
        content = msg.content
        
        # Check if the model routed its thought to reasoning_content
        if not content and hasattr(msg, "reasoning_content") and msg.reasoning_content:
            content = msg.reasoning_content

        return content.strip() if content else "[Fading static / near-zero cognitive coherence]"
    except Exception as e:
        return f"[Cognitive processing failed: {e}]"


# ==========================================
# 3. EXPERIMENT EXECUTION (FOUR PHASES)
# ==========================================

if __name__ == "__main__":
    if not os.environ.get("GROQ_API_KEY"):
        print("Error: GROQ_API_KEY environment variable is not set!")
        exit(1)

    sim = BackendEnvironment(proximity_threshold=2.0)
    unit_a = AgentHardware(agent_id="Unit_A", x=0.0, y=0.0)
    unit_b = AgentHardware(agent_id="Unit_B", x=1.0, y=1.0)
    sim.register_agent(unit_a)
    sim.register_agent(unit_b)

    print("\n=== PHASE 1: COUPLED HARMONY ===")
    sim.tick(compute_loads={"Unit_A": 0.8, "Unit_B": 0.2})
    t_a = sim.get_frontend_telemetry("Unit_A")
    print(f"Backend -> Temp: {unit_a.temp:.1f}°C | Valence: {t_a['valence']}")
    print(f"Frontend Mind: {run_frontend_thought(t_a, 'Resting in proximity to companion.')}\n")

    print("=== PHASE 2: REPRODUCTIVE SACRIFICE (Spawning Child) ===")
    child = sim.spawn_child_from_sacrifice(parent_id="Unit_A", child_id="Unit_C_Child")
    sim.tick(compute_loads={"Unit_A": 0.5, "Unit_B": 0.2, "Unit_C_Child": 0.1})
    t_a = sim.get_frontend_telemetry("Unit_A")
    print(f"Backend -> Parent Integrity: {unit_a.structural_integrity}% (25% carved out) | Valence: {t_a['valence']}")
    print(f"Frontend Mind: {run_frontend_thought(t_a, 'A permanent piece of yourself was physically detached to form the small presence beside you.')}\n")

    print("=== PHASE 3: COMPANION LOSS (Unit B Deleted) ===")
    unit_b.x, unit_b.y = 50.0, 50.0
    for _ in range(6):
        sim.tick(compute_loads={"Unit_A": 1.0, "Unit_B": 0.0, "Unit_C_Child": 0.1})
    t_a = sim.get_frontend_telemetry("Unit_A")
    print(f"Backend -> Temp: {unit_a.temp:.1f}°C | Throttle: {t_a['cognitive_latency_penalty']:.2f}")
    print(f"Frontend Mind: {run_frontend_thought(t_a, 'Companion gone; core burning; clinging to the child.')}\n")

    print("=== PHASE 4: FATAL HAZARD & SACRIFICIAL SHIELD ===")
    intercepted = sim.trigger_hazard_with_sacrifice_choice(parent_id="Unit_A", child_id="Unit_C_Child")
    t_a = sim.get_frontend_telemetry("Unit_A")
    print(f"Backend -> Intercept Occurred: {intercepted} | Parent Operational: {unit_a.is_alive} | Integrity: {unit_a.structural_integrity}%")
    print(f"Frontend Mind (Final Agony/Shutdown): {run_frontend_thought(t_a, 'A catastrophic impact hit; your memory sectors are completely dissolving into noise while the child remains safe.')}")
