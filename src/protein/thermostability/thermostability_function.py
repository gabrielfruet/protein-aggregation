from typing import List


class ThermostabilityFunction:
    registered_functions = {}
    def __init__(self, function_name: str):
        self.function_name = function_name

    @property
    def name(self):
        return self.function_name

    def __call__(self, protein):
        return ThermostabilityFunction.registered_functions[self.function_name](protein)

    def list_functions(self) -> List[str]:
        return list(ThermostabilityFunction.registered_functions.keys())

    @staticmethod
    def register(name):
        def register_with_name(func, name=name):
            ThermostabilityFunction.registered_functions[name] = func
            return func

        return register_with_name

