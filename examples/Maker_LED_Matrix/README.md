# display server for [e-radionica](https://e-radionica.com/en/blog/maker-led-display-everything-in-one-place) LED matrix display
- ESP12 reflashed with micropython
- server (AP) sends beacon to **230.1:7000** and receives its commands/payload at the advertised source address (UDP)
- payload is either a full screen image or a matrix driver **function register** dump (index+data)
