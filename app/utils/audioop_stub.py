import sys
import types

# Create a dummy audioop module for Python 3.13 compatibility
audioop_stub = types.ModuleType("audioop")

def _not_implemented(*args, **kwargs):
    raise NotImplementedError("audioop module is no longer available in Python 3.13")

# Define all expected stubs used by pydub
for func_name in [
    "add", "adpcm2lin", "avg", "avgpp", "bias", "byteswap",
    "cross", "findfactor", "findfit", "findmax", "getsample",
    "lin2adpcm", "lin2alaw", "lin2lin", "lin2ulaw",
    "max", "maxpp", "minmax", "mul", "reverse", "rms",
    "tomono", "tostereo", "ulaw2lin", "addsample",
    "getsample", "ratecv"
]:
    setattr(audioop_stub, func_name, _not_implemented)

sys.modules["audioop"] = audioop_stub
