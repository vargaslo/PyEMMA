'''
Created on 23.01.2015

@author: marscher
'''
import tempfile
import unittest

import mdtraj
import pkg_resources

import numpy as np
from pyemma.coordinates.coordinate_transformation.transform.transformer import Transformer
from pyemma.coordinates.coordinate_transformation.io.featurizer import Featurizer
from pyemma.coordinates.coordinate_transformation.io.feature_reader import FeatureReader


def map_return_input(traj):
    return traj.xyz


class MemoryStorage(Transformer):

    def __init__(self, chunksize=100, lag=0):
        Transformer.__init__(self, chunksize, lag)

        self.lagged_chunks = []
        self.final = None
        self._param_finished = False

    def param_add_data(self, X, itraj, t, first_chunk, last_chunk_in_traj, last_chunk, ipass, Y=None):
        self.lagged_chunks.append(Y)
        # print t
        if last_chunk:
            # TODO: fix shape
            new_shape = ()
            # .reshape((2, 1000, 2, 3))
            self.final = np.array(self.lagged_chunks)
            self._param_finished = True


class TestFeatureReader(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        c = super(TestFeatureReader, cls).setUpClass()
        # create a fake trajectory which has 2 atoms and coordinates are just a range
        # over all frames.
        cls.trajfile = tempfile.mktemp('.xtc')
        xyz = np.arange(1000 * 2 * 3).reshape((1000, 2, 3))
        cls.topfile = pkg_resources.resource_filename(
            'test_featurereader', 'data/test.pdb')
        t = mdtraj.load(cls.topfile)
        t.xyz = xyz
        t.time = np.arange(1000)
        t.save(cls.trajfile)
        return c

    def testTimeLaggedAccess(self):
        # each frame has 2 atoms with 3 coords = 6 coords per frame.
        # coords are sequential through all frames and start with 0.
        trajfiles = [self.trajfile]

        # so first lagged frame is 18, since 3 frames a 6 coords are skipped
        lags = [1, 3, 5, 10, 29, 100]

        chunksizes = [2, 3, 7, 11, 10, 101]

        for lag in lags:
            for chunksize in chunksizes:
                if chunksize <= lag:
                    continue
                print "lag: %s; chunksize: %s " % (lag, chunksize)
                f = Featurizer(self.topfile)
                f.map = map_return_input

                reader = FeatureReader(trajfiles, self.topfile, f)

                m = MemoryStorage(lag=lag)
                m.data_producer = reader
                chain = [f, reader, m]
                for t in chain:
                    t.chunksize = chunksize

                m.parametrize()

                frist_lagged_chunk = m.lagged_chunks[0]
                self.assertEqual(frist_lagged_chunk.shape[0], chunksize)

                n_coords = 3 * 2 * 10 * chunksize
                coords = np.arange(n_coords).reshape((n_coords / 6, 2, 3))

                # first lagged chunk should start at lag and stop at chunksize +
                # lag
                np.testing.assert_allclose(
                    frist_lagged_chunk, coords[lag:chunksize + lag])
                # TODO: check last lagged frame


if __name__ == "__main__":
    unittest.main()
