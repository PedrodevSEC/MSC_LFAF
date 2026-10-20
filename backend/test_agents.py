from pprint import pprint

from services.agent_service import AgentService


service = AgentService()

measurements = [
    {"bpm": 80},
    {"bpm": 84},
    {"bpm": 90},
    {"bpm": 100},
]

result = service.process_measurements(
    measurements=measurements,
    baseline_bpm=65,
)

pprint(result)