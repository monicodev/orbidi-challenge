import math

class MetricCalculator:
    """
    Handles the mathematical logic for lead conversion probability.
    """

    @staticmethod
    def sigmoid(x: float) -> float:
        """
        Standard Sigmoid function: 1 / (1 + exp(-x))
        Includes limits to prevent math overflow errors.
        """
        # Clamp x to avoid extreme values that crash math.exp
        x = max(min(x, 100), -100)
        return 1 / (1 + math.exp(-x))

    def calculate_conversion_metric(
        self, 
        rentability: int, 
        typology_val: int, 
        distance_m: float
    ) -> float:
        """
        Calculates the metric based on:
        - Rentability: 0-100 (normalized to 0.0-1.0)
        - Typology: 1-1000 (normalized to 0.0-1.0)
        - Proximity: 1 / (1 + distance)
        """
        # Normalization
        r = rentability / 100
        t = typology_val / 1000
        p = 1 / (1 + distance_m)

        # Formula: sigmoid(0.2*r + 0.4*t + 0.4*p)
        x = (0.2 * r) + (0.4 * t) + (0.4 * p)
        
        return self.sigmoid(x)

# Singleton instance
calculator = MetricCalculator()