import numpy as np
import matplotlib.pyplot as plt
import neurokit2 as nk
import pandas as pd

ecg = np.load("ecg_data.npy")

signals, info = nk.ecg_process(ecg, sampling_rate=130)
nk.ecg_plot(signals, info)

peaks, info = nk.ecg_peaks(ecg, sampling_rate=130)

hrv = nk.hrv(peaks, sampling_rate=130, show=True)

ecg_rate = nk.ecg_rate(peaks, sampling_rate=130, desired_length=len(ecg))

edr_df = pd.DataFrame({
    "Van Gent et al.": nk.ecg_rsp(ecg_rate, sampling_rate=130),
    "Charlton et al." : nk.ecg_rsp(ecg_rate, sampling_rate=130, method="charlton2016"),
    "Soni et al.": nk.ecg_rsp(ecg_rate, sampling_rate=130, method="soni2019"),
    "Sarkar et al.": nk.ecg_rsp(ecg_rate, sampling_rate=130, method="sarkar2015")
    })

nk.signal_plot(edr_df, subplots=True)

plt.show()