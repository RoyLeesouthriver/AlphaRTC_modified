conda activate A3C
rm thoughtput.png
rm vmaf.png
rm metrics.png
rm loss.png
rm loss_percent.png
rm output.json
python3 test.py
python3 plot.py
python3 throughput.py