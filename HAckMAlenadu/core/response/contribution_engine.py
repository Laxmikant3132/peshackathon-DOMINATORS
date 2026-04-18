class ContributionEngine:
    """
    Weighted Feature Scaling Model.
    Decodes the 'Black Box' of detection by assigning a contribution score 
    to every telemetry field that triggered the incident.
    """
    def generate_breakdown(self, signals):
        if not signals:
            return {"status": "baseline", "contributions": {}}

        total_weight = sum(s.get("weight", 0.1) for s in signals)
        
        contributions = {}
        for s in signals:
            feature = s.get("feature", "unknown")
            weight = s.get("weight", 0.1)
            
            # Weighted normalization to 100%
            percentage = round((weight / total_weight) * 100, 1)
            contributions[feature] = contributions.get(feature, 0) + percentage

        # Sorting by most significant contribution
        sorted_contribs = dict(sorted(contributions.items(), key=lambda item: item[1], reverse=True))
        
        return {
            "status": "alert_triggered",
            "weighted_breakdown": sorted_contribs,
            "primary_driver": list(sorted_contribs.keys())[0] if sorted_contribs else "unknown"
        }

    def justify_confidence(self, signal_count, avg_weight):
        """
        Provides a mathematical justification for the confidence score.
        High Confidence = High Signal Count + High Weighted Influence.
        """
        score = min(1.0, (signal_count * 0.2) + (avg_weight * 0.5))
        
        if score > 0.8:
            reasoning = "Multi-signal correlation with high-weight feature overlap."
        elif score > 0.5:
            reasoning = "Statistical anomaly detected with secondary rule confirmation."
        else:
            reasoning = "Low-signal observation requiring further forensic triage."
            
        return round(score, 2), reasoning
