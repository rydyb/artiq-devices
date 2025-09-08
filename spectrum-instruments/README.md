# Spectrum Instruments

Spectrum Instruments integration into the ARTIQ timing system.

## Install

Create a virtual environment:
```shell
python -m venv .venv
```

To activate the virtual environment:
```shell
source .venv/bin/activate
```

Install the dependencies (if not done already):
```shell
pip install .
```

## Usage

### Standalone

List devices:
```shell
python spectrum_instruments.main list
```

Output a singletone:
```shell
python spectrum_instruments.main tone \
    --serial-number 18996 \
    --frequency 200e6
```

Output a pulse on an external trigger signal:
```shell
python spectrum_instruments.main pulse \
    --serial-number 18996 \
    --frequency 200e6 \
    --duration 100e-6
```

Output a sweep on an external trigger signal:
```shell
python spectrum_instruments.main sweep \
    --serial-number 18996 \
    --center 200e6 \
    --span 20e6 \
    --duration 100e-6
```

### Remote control via ARTIQ

Launch an RPC server:
```shell
python spectrum_instruments.main rpc \
    --serial-number 18996
```

Add the device to your `device_db.py`:
```python
device_db.update(
    {
        "rydberg_siggen": {
            "type": "controller",
            "host": "bec-ex-232.rydyb.bec.physik.uni-muenchen.de",
            "port": 3249,
        },
    }
)
```

Use you the `rydberg_siggen` inside your experimental sequence:
```python
class RydbergExperiment(EnvExperiment):

    def build(self):
        self.setattr_device("core")
        self.setattr_device("phaser0")
        self.setattr_device("ttl0")
        self.setattr_device("ttl1")
        self.setattr_device("rydberg_siggen")

    @kernel
    def run(self):
        self.core.reset()
        self.core.break_realtime()
        delay(1 * ms)

        self.rydberg_siggen.pulse(
            frequency=200e6,
            duration=50e-9,
        )

        while True:
            self.trigger()
            delay(1 * ms)

    @kernel
    def trigger(self):
        with parallel:
            self.ttl0.pulse(10 * us)
            self.ttl1.pulse(10 * us)
```

## Develop

```shell
cd spectrum_instruments
python -m venv .venv
source .venv/bin/activate
pip install -e .
```