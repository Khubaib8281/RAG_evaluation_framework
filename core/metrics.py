import time

class MetricsTracker:
    def __init__(self):
        self.start_time = None
        
    def start(self):
        self.start_time = time.time()
        
    def stop(self):
        return (time.time() - self.start_time()) * 1000
    

def estimate_tokens(text):
        return len(text.split())