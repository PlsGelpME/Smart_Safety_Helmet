from machine import PWM
import time

class Buzzer:
    def __init__(self, pin):
        self.buzzer = PWM(pin)
        self.buzzer.duty_u16(0)

        self.step = 0
        self.last_time = time.ticks_ms()
        self.state = False

    def _on(self, freq):
        self.buzzer.freq(freq)
        self.buzzer.duty_u16(32768)

    def _off(self):
        self.buzzer.duty_u16(0)

    # --------------------------------------------------------
    # 1. Helmet not worn alert – triple short 2500 Hz beeps
    # --------------------------------------------------------
    def helmet_alert(self):
        now = time.ticks_ms()
        if time.ticks_diff(now, self.last_time) < 100:
            return

        self.last_time = now

        if self.step % 2 == 0:
            self._on(2500)
        else:
            self._off()

        self.step += 1
        if self.step > 5:
            self.step = 0

    # --------------------------------------------------------
    # 2. Gas alert – ON/OFF 1800 Hz every 500 ms
    # --------------------------------------------------------
    def gas_alert(self):
        now = time.ticks_ms()
        if time.ticks_diff(now, self.last_time) >= 500:
            self.last_time = now
            self.state = not self.state

            if self.state:
                self._on(1800)
            else:
                self._off()

    # --------------------------------------------------------
    # 3. Faint emergency – SOS Morse pattern @ 1000 Hz
    # --------------------------------------------------------
    def faint_alert(self):
        now = time.ticks_ms()

        if self.step < 6:
            duration = 200
        elif self.step < 12:
            duration = 600 if self.step % 2 == 0 else 200
        elif self.step < 18:
            duration = 200
        else:
            duration = 1500

        if time.ticks_diff(now, self.last_time) >= duration:
            self.last_time = now

            if self.step < 18:
                if self.step % 2 == 0:
                    self._on(1000)
                else:
                    self._off()
                self.step += 1
            else:
                self.step = 0

    # --------------------------------------------------------
    # To silence buzzer (useful in main file)
    # --------------------------------------------------------
    def stop(self):
        self._off()
        self.step = 0
