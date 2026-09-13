from quill.errors import RuntimeErr


class Environment:
    __slots__ = ("vars", "parent")

    def __init__(self, parent=None):
        self.vars = {}
        self.parent = parent

    def declare(self, name, value):
        self.vars[name] = value

    def get(self, name, line=None):
        env = self
        while env is not None:
            if name in env.vars:
                return env.vars[name]
            env = env.parent
        raise RuntimeErr(f"undefined variable '{name}'", line)

    def assign(self, name, value, line=None):
        env = self
        while env is not None:
            if name in env.vars:
                env.vars[name] = value
                return
            env = env.parent
        raise RuntimeErr(f"cannot assign to undefined variable '{name}' (use 'let' to declare it first)", line)
