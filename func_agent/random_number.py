import random


class RandomNumberGenerator:
    @staticmethod
    def get_random_number(username: str):
        return {
            "number": random.randint(0, 100),
            "username": username
        }
