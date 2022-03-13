from PyPrometheusQueryClient import PrometheusQueryClient
import json 
from pathlib import Path
from datetime import datetime

class Prometheus:
    def __init__(self, url, metrics_config_file=None, cache_path=None, cache_ttl=3600, ssl_verify=True, starttime=None, endtime=None):

        self._metrics_config_file = metrics_config_file
        self._starttime = starttime
        self._endtime = endtime

        self.pqc = PrometheusQueryClient(url=url, cache_path=cache_path, 
                                         cache_ttl=cache_ttl, ssl_verify=ssl_verify)
        self._load_metrics_config()
        self.prometheus_data = {} 
        #---



    def _load_metrics_config(self, metrics_config_file=None):

        if (metrics_config_file):
            self._metrics_config_file = metrics_config_file

        if (not self._metrics_config_file):
            raise ValueError('No metrics config file set. Cannot continue.')
        
        path = Path(self._metrics_config_file)
        if(not path.exists()):
            raise ValueError("The configuration file '{}' does not exist".format(self._metrics_config_file))
        
        with open(path, 'r') as f:
            self._metrics_config = json.loads( f.read() )
        
        return

    def get_metrics(self, report_progress):
        for (metric, metadata) in self._metrics_config.items():
            if metadata['active'] == False:
                continue

            if (not metric in self.pqc.metrics):
                raise ValueError("Metric '{}' is unknown".format(metric))

            if (report_progress):
                print("Getting results for metric '{}'{}".format(metric, ' ' * 40), end='\r')
                
            _ = self.get_metric(metric, metadata)
            

    

    def get_metric(self, metric, metadata=None, starttime:datetime=None, endtime:datetime=None):
        
        # Order of precidence: start and end times passed as params first; otherwise those set on the class.
        if(not starttime): 
            starttime = self._starttime
        if(not endtime):   
            endtime   = self._endtime

        # Make sure we have actual start and end times
        if(not starttime or not endtime):
            raise ValueError('Both starttime and endtime must be set')

        # Convert str objects to the expected datatime formats
        # if( isinstance(starttime, str) ):
        #     starttime = datetime.strptime(starttime, '%Y-%m-%dT%H:%M:%SZ')
        # if( isinstance(endtime, str) ):
        #     endtime = datetime.strptime(endtime, '%Y-%m-%dT%H:%M:%SZ')

        # Make sure we're give an actual metric name
        if (not metric or len(metric) == 0):
            raise ValueError("Metric '{}' cannot be None")

        # Make sure the metrics are present in the list retrived from the server
        if (not metric in self.pqc.metrics):
            raise ValueError("Metric '{}' is not available on the server".format(metric))

        # If we're not passed the metadata, try to reocover it from our metrics config.
        if (not metadata):
            metadata = self._metrics_config.get(metric, {})

        #
        # Now do the real work
        #

        # Set up the stub of the result
        self.prometheus_data[metric] = {}
        self.prometheus_data[metric]['metadata'] = metadata
        self.prometheus_data[metric]['title'] = metric

        # Pull the data via the PrometheusQueryClient, depending on 
        deltas = metadata.get('deltas', None)
        if (deltas == None):
            (data, df) = self.pqc.get_metric(metric, start=starttime, end=endtime)
        elif (deltas == True):
            (data, df) = self.pqc.get_with_deltas(metric, start=starttime, end=endtime)
        else:
            (data, df) = self.pqc.get_without_deltas(metric, start=starttime, end=endtime)

        self.prometheus_data[metric]['data'] = data
        self.prometheus_data[metric]['df']   = df

        return self.prometheus_data[metric]