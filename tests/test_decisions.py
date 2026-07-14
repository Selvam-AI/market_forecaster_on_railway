from geopolitical_market_forecaster.decisions import build_sector_decisions


def test_sector_decisions_turn_oil_shipping_risk_into_demo_signals():
    decisions = build_sector_decisions(
        [
            {
                "title": "Houthi attacks disrupt Red Sea shipping",
                "source": "Test",
                "url": "https://example.com/red-sea",
                "summary": "Oil supply disruption and shipping insurance costs rise.",
                "signal_tier": "Actionable",
                "themes": ["energy supply", "shipping risk"],
                "affected_markets": ["energy", "shipping"],
                "rationale": "Oil supply and shipping risk detected.",
                "forecast": "Oil and shipping risk premium may rise.",
                "confidence": "Medium",
                "approved": True,
                "flags": [],
            }
        ]
    )

    offshore = decisions[0]
    airline = decisions[1]

    assert offshore["category"] == "Offshore & Marine Exposure"
    assert offshore["decision"] == "BUY"
    assert "Seatrium" in offshore["candidates"]
    assert offshore["evidence"]
    assert offshore["confidence_score"] == 58
    assert offshore["wind_direction"] == "TAILWIND"
    assert offshore["market_price"] == "S$1.97"
    assert offshore["logic_score"] == 74
    assert offshore["evidence"][0]["topic"] == "Shipping"
    assert offshore["agent_steps"][0]["agent"] == "Scraper Agent"
    assert offshore["theme"] == "offshore"

    assert airline["category"] == "Airline Exposure"
    assert airline["decision"] == "AVOID"
    assert "Singapore Airlines" in airline["candidates"]
    assert airline["evidence"]
    assert airline["confidence_score"] == 61
    assert airline["wind_direction"] == "HEADWIND"
    assert airline["market_price"] == "S$7.62"
    assert airline["logic_score"] == 81
    assert airline["agent_steps"][-1]["agent"] == "Governor Agent"
    assert airline["theme"] == "airline"
