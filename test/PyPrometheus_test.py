import unittest
from PyPrometheus import Prometheus
from pathlib import Path
import urllib3
from datetime import datetime, timedelta

urllib3.disable_warnings()

def delete_folder(pth:Path) -> None:
    if (pth.exists()):
        for sub in pth.iterdir():
            if (sub.is_dir()):
                delete_folder(sub)
            else:
                sub.unlink()
        pth.rmdir()
    return


class TestPyPrometheus(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # FIXME: Fragile test. Hardcoded endpoint.
        # FIXME: Fragile test. Assumes a the endpoint is available
        cls.api_url = "https://azlappjaegrs1.mfcgd.com/prometheus/" 
        cls.ssl_verify = False 
        cls.configfile = Path('./lib/blakemere/test/metrics_conf.json')
        cls.filename   = Path('./lib/blakemere/test/testdata.csv')
        cls.cache_path = Path('./test/TestPyJaegerAnalysis/.prometheus_cache/')

        return    

    def setUp(self) -> None:
        delete_folder(self.cache_path)
        return super().setUp()


    def _instantiate_instance(self):
        iut = Prometheus(self.api_url, metrics_config_file=self.configfile, cache_path=self.cache_path, ssl_verify=self.ssl_verify)
        return iut

    @unittest.skip
    def test_constructor(self):
        iut = self._instantiate_instance()
        self.assertIsNotNone( iut )
        return

    @unittest.skip
    def test_load_metrics_config(self):

        iut = self._instantiate_instance()

        # The object should have a _load_metrics_config attribute
        self.assertTrue( hasattr(iut, '_load_metrics_config' ) )

        # Run the method, with a passed config file
        iut._load_metrics_config(self.configfile)

        self.assertTrue( hasattr(iut, '_metrics_config' ) )
        self.assertIsNotNone( iut._metrics_config )

        # Make sure we loaded what we expected
        self.assertIsNotNone( iut._metrics_config.get('node_disk_read_bytes_total', None))
        self.assertIsNotNone( iut._metrics_config.get('node_filesystem_avail_bytes', None) )
        self.assertIsNotNone( iut._metrics_config.get('node_load1', None) )

        return


    @unittest.skip
    def test_load_metrics_config_exception_no_metrics_file(self):

        iut = self._instantiate_instance()

        expected_exception = False
        expected_exception_msg = 'No metrics config file set. Cannot continue.'

        try:    
            iut._load_metrics_config()
        except ValueError as e: 
            if(e.args[0] == expected_exception_msg):
                expected_exception =True
        except Exception as e:
            self.fail('Recevied an unexpected exception: {}'.format(e))            

        self.assertTrue(expected_exception)

        return


    @unittest.skip
    def test_load_metrics_config_exception_metrics_file_does_not_exist(self):

        iut = self._instantiate_instance()
        path = Path('./does_not_exist.conf')
        if(path.exists()):
            raise ValueError("The file '{}' shouldn't exist fopr this test, yet it actually does. Weird!".format(path))

        expected_exception = False
        expected_exception_msg = "The configuration file '{}' does not exist".format(path)

        try:    
            iut._load_metrics_config(path)
        except ValueError as e: 
            if(e.args[0] == expected_exception_msg):
                expected_exception =True
        except Exception as e:
            self.fail('Recevied an unexpected exception: {}'.format(e))            

        self.assertTrue(expected_exception)

        return


    @unittest.skip
    def test_get_metrics(self):
        self.assertFalse( True )
        return


    #@unittest.skip
    def test_get_metric(self):
        iut = self._instantiate_instance()

        metric = list(iut._metrics_config.keys())[0]

        endtime = datetime.now()
        starttime = endtime - timedelta(hours=1)

        result = iut.get_metric(metric, starttime=starttime, endtime=endtime)
        

        self.assertIsNotNone( result )
        result_item = iut.prometheus_data.get(metric, None)
        self.assertIsNotNone( result_item )
        self.assertIsNotNone( result_item.get('data', None))
        self.assertIsNotNone( result_item.get('df', None))

        return



if (__name__ == '__main__'):
    unittest.main()
    
