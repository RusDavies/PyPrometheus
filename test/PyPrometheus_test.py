import unittest
from PyPrometheus import Prometheus
from pathlib import Path
import urllib3
from datetime import datetime, timedelta
import json

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
        with open('./test/config_test_TestPyPrometheus.json', 'r') as file:
            tmp = file.read()
            cls.test_config = json.loads(tmp)

        # Fixup file and path strings into Path objects
        for item in ['cache_path', 'metrics_config_file']:
            cls.test_config[item]  = Path(cls.test_config[item])

        # Get our metrics configuration 
        with open(cls.test_config['metrics_config_file'], 'r') as file:
            tmp = file.read()
            cls.metrics = json.loads(tmp)

        cls.api_url    = cls.test_config['url']
        cls.ssl_verify = cls.test_config['ssl_verify'] 
        cls.configfile = cls.test_config['metrics_config_file']
        cls.filename   = cls.test_config['test_data']
        cls.cache_path = cls.test_config['cache_path']

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
    
