import streamlit as st
import numpy as np
from datetime import datetime, timezone, timedelta
from event_clock import EventClockConfig
from window_config import TumblingWindowConfig

def build_array():
    return np.empty((0,3))

def acc_values(np_array, ticker):
    return np.insert(np_array, 0, np.array((ticker.time, ticker.price, ticker.dayVolume)), 0)

def get_event_time(ticker):
    return datetime.utcfromtimestamp(ticker.time/1000).replace(tzinfo=timezone.utc)

cc = EventClockConfig(get_event_time, wait_for_system_duration=timedelta(seconds=10))

start_at = datetime.now(timezone.utc)
start_at = start_at - timedelta(
    seconds=start_at.second, microseconds=start_at.microsecond
)
wc = TumblingWindowConfig(start_at=start_at, length=timedelta(seconds=60))

# Streamlit app
def main():
    st.title("Streamlit App with Event Clock and Tumbling Window")
    
    # You can add Streamlit components here to interact with the data
    
if __name__ == "__main__":
    main()
