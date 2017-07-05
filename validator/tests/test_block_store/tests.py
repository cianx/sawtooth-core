# Copyright 2017 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ------------------------------------------------------------------------------

import logging
import unittest

from sawtooth_validator.database.dict_database import DictDatabase
from sawtooth_validator.exceptions import ChainHeadUpdatedError
from sawtooth_validator.exceptions import PossibleForkDetectedError
from sawtooth_validator.journal.block_store import BlockStore
from sawtooth_validator.journal.block_wrapper import NULL_BLOCK_IDENTIFIER
from sawtooth_validator.journal.block_wrapper import BlockWrapper

from sawtooth_validator.protobuf.block_pb2 import Block
from sawtooth_validator.protobuf.block_pb2 import BlockHeader

from test_journal.block_tree_manager import BlockTreeManager


LOGGER = logging.getLogger(__name__)


class BlockStoreTest(unittest.TestCase):

    def setUp(self):
        self.block_tree_manager = BlockTreeManager()

    def test_chain_head(self):
        block = self.create_block()
        block_store = self.create_block_store(
            {
                'chain_head_id': 'head',
                'head': self.encode_block(block)
            })
        chain_head = block_store.chain_head
        self.assert_blocks_equal(chain_head, block)

    def test_get(self):
        block = self.create_block()
        block_store = self.create_block_store(
            {
                'chain_head_id': 'head',
                'head': self.encode_block(block),
                'txn': 'head'
            })
        chain_head = block_store['head']
        self.assert_blocks_equal(chain_head, block)

        with self.assertRaises(KeyError):
            block_store['txn']

        with self.assertRaises(KeyError):
            chain_head = block_store['missing']

    def test_set(self):
        block = self.create_block()
        block_store = self.create_block_store(
            {
                'chain_head_id': 'head',
                'head': self.encode_block(block),
                'txn': 'head'
            })
        block2 = self.create_block()
        with self.assertRaises(KeyError):
            block_store['head'] = block2

        block_store[block2.identifier] = block2

        stored_block = block_store[block2.identifier]
        self.assert_blocks_equal(stored_block, block2)

        with self.assertRaises(AttributeError):
            block_store['batch'] = 'head'

    def test_has(self):
        block_store = self.create_block_store(
            {
                'chain_head_id': 'block',
                'block': self.create_serialized_block(),
                'txn': 'block',
                'batch': 'block'
            })

        self.assertTrue(block_store.has_transaction('txn'))
        self.assertFalse(block_store.has_transaction('txn_missing'))
        self.assertTrue(block_store.has_batch('batch'))
        self.assertFalse(block_store.has_transaction('batch_missing'))

        with self.assertRaises(ChainHeadUpdatedError):
            block_store.has_transaction('txn', 'old_head')

        with self.assertRaises(ChainHeadUpdatedError):
            block_store.has_transaction('txn_missing', 'old_head')

        with self.assertRaises(ChainHeadUpdatedError):
            block_store.has_batch('batch', 'old_head')

        with self.assertRaises(ChainHeadUpdatedError):
            block_store.has_transaction('batch_missing', 'old_head')

        self.assertTrue('block' in block_store)
        self.assertTrue('batch' in block_store)
        self.assertTrue('txn' in block_store)

        self.assertFalse('block_missing' in block_store)
        self.assertFalse('batch_missing' in block_store)
        self.assertFalse('txn_missing' in block_store)

    def test_get_block_by_batch_id(self):
        block = self.create_block()
        block_store = self.create_block_store()
        block_store.update_chain([block])
        chain_head_id = block.header_signature

        batch_id = block.batches[0].header_signature
        stored = block_store.get_block_by_batch_id(batch_id)
        self.assert_blocks_equal(stored, block)

        with self.assertRaises(KeyError):
            block_store.get_block_by_batch_id("bad")

        #  repeat same test but verify the head assertion works
        stored = block_store.get_block_by_batch_id(batch_id, chain_head_id)
        self.assert_blocks_equal(stored, block)

        with self.assertRaises(ChainHeadUpdatedError):
            block_store.get_block_by_batch_id(batch_id, "old_head")

        with self.assertRaises(ChainHeadUpdatedError):
            block_store.get_block_by_batch_id("bad", "old_head")


    def test_get_batch_by_transaction(self):
        block = self.create_block()
        chain_head_id = block.header_signature
        block_store = self.create_block_store()
        block_store.update_chain([block])

        batch = block.batches[0]
        txn_id = batch.transactions[0].header_signature
        stored = block_store.get_batch_by_transaction(txn_id)
        self.asset_protobufs_equal(stored, batch)

        with self.assertRaises(KeyError):
            block_store.get_batch_by_transaction("bad")

        #  repeat same test but verify the head assertion works
        stored = block_store.get_batch_by_transaction(txn_id, chain_head_id)
        self.asset_protobufs_equal(stored, batch)

        with self.assertRaises(ChainHeadUpdatedError):
            block_store.get_batch_by_transaction(txn_id, "old_head")

        with self.assertRaises(ChainHeadUpdatedError):
            block_store.get_batch_by_transaction("bad", "old_head")


    def test_get_block_by_transaction_id(self):
        block = self.create_block()
        chain_head_id = block.header_signature
        block_store = self.create_block_store()
        block_store.update_chain([block])

        txn_id = block.batches[0].transactions[0].header_signature
        stored = block_store.get_block_by_transaction_id(txn_id)
        self.assert_blocks_equal(stored, block)

        with self.assertRaises(KeyError):
            stored = block_store.get_block_by_transaction_id("bad")

        #  repeat same test but verify the head assertion works
        stored = block_store.get_block_by_transaction_id(txn_id, chain_head_id)
        self.assert_blocks_equal(stored, block)

        with self.assertRaises(ChainHeadUpdatedError):
            block_store.get_block_by_transaction_id(txn_id, "old_head")

        with self.assertRaises(ChainHeadUpdatedError):
            block_store.get_block_by_transaction_id("bad", "old_head")


    def test_get_batch(self):
        block = self.create_block()
        chain_head_id = block.header_signature
        block_store = self.create_block_store()
        block_store.update_chain([block])

        batch = block.batches[0]
        batch_id = batch.header_signature
        stored = block_store.get_batch(batch_id)
        self.asset_protobufs_equal(stored, batch)

        with self.assertRaises(KeyError):
            stored = block_store.get_batch("bad")

        #  repeat same test but verify the head assertion works
        stored = block_store.get_batch(batch_id, chain_head_id)
        self.asset_protobufs_equal(stored, batch)

        with self.assertRaises(ChainHeadUpdatedError):
            block_store.get_batch(batch_id, "old_head")

        with self.assertRaises(ChainHeadUpdatedError):
            block_store.get_batch("bad", "old_head")

    def test_get_transaction(self):
        block = self.create_block()
        chain_head_id = block.header_signature
        block_store = self.create_block_store()
        block_store.update_chain([block])

        txn = block.batches[0].transactions[0]
        txn_id = txn.header_signature
        stored = block_store.get_transaction(txn_id)
        self.asset_protobufs_equal(stored, txn)

        with self.assertRaises(KeyError):
            stored = block_store.get_transaction("bad")

        #  repeat same test but verify the head assertion works
        stored = block_store.get_transaction(txn_id, chain_head_id)
        self.asset_protobufs_equal(stored, txn)

        with self.assertRaises(ChainHeadUpdatedError):
            block_store.get_transaction(txn_id, "old_head")

        with self.assertRaises(ChainHeadUpdatedError):
            block_store.get_transaction("bad", "old_head")

    def assert_blocks_equal(self, stored, reference):
        self.asset_protobufs_equal(stored.block,
                                  reference.block)

    def asset_protobufs_equal(self, stored, reference):
        self.assertEqual(self.encode(stored),
                         self.encode(reference))

    @staticmethod
    def create_block_store(data=None):
        return BlockStore(DictDatabase(data))

    def create_block(self):
        return self.block_tree_manager.create_block()

    def create_serialized_block(self):
        block_wrapper = self.block_tree_manager.create_block()
        return block_wrapper.block.SerializeToString()

    @staticmethod
    def encode_block(obj):
        return obj.block.SerializeToString()

    @staticmethod
    def encode(obj):
        return obj.SerializeToString()


class BlockStorePredecessorIteratorTest(unittest.TestCase):

    def test_iterate_chain(self):
        """Given a block store, create an predecessor iterator.

        1. Create a chain of length 5.
        2. Iterate the chain using the get_predecessor_iter from the chain head
        3. Verify that the block ids match the chain, in reverse order
        """

        block_store = BlockStore(DictDatabase())
        chain = self._create_chain(5)
        block_store.update_chain(chain)

        ids = [b.identifier for b in block_store.get_predecessor_iter()]

        self.assertEqual(
            ['abcd4', 'abcd3', 'abcd2', 'abcd1', 'abcd0'],
            ids)

    def test_iterate_chain_from_starting_block(self):
        """Given a block store, iterate if using an predecessor iterator from
        a particular start point in the chain.

        1. Create a chain of length 5.
        2. Iterate the chain using the get_predecessor_iter from block 3
        3. Verify that the block ids match the chain, in reverse order
        """
        block_store = BlockStore(DictDatabase())
        chain = self._create_chain(5)
        block_store.update_chain(chain)

        block = block_store['abcd2']

        ids = [b.identifier
               for b in block_store.get_predecessor_iter(block)]

        self.assertEqual(
            ['abcd2', 'abcd1', 'abcd0'],
            ids)

    def test_iterate_chain_on_empty_block_store(self):
        """Given a block store with no blocks, iterate using predecessor iterator
        and verify that it results in an empty list.
        """
        block_store = BlockStore(DictDatabase())

        self.assertEqual([], [b for b in block_store.get_predecessor_iter()])

    def test_fork_detection_on_iteration(self):
        """Given a block store where a fork occurred while using the predecessor
        iterator, it should throw a PossibleForkDetectedError.

        The fork occurrance will be simulated.
        """
        block_store = BlockStore(DictDatabase())
        chain = self._create_chain(5)
        block_store.update_chain(chain)

        iterator = block_store.get_predecessor_iter()

        self.assertEqual('abcd4', next(iterator).identifier)

        del block_store['abcd3']

        with self.assertRaises(PossibleForkDetectedError):
            next(iterator)

    def _create_chain(self, length):
        chain = []
        previous_block_id = NULL_BLOCK_IDENTIFIER
        for i in range(length):
            block = BlockWrapper(
                Block(header_signature='abcd{}'.format(i),
                      header=BlockHeader(
                          block_num=i,
                          previous_block_id=previous_block_id
                      ).SerializeToString()))

            previous_block_id = block.identifier

            chain.append(block)

        chain.reverse()

        return chain
