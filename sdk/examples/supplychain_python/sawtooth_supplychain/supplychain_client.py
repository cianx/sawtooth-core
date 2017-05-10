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

import hashlib
import logging
import base64
import urllib.request
import time

import json

import sawtooth_sdk.protobuf.batch_pb2 as batch_pb2
import sawtooth_sdk.protobuf.transaction_pb2 as transaction_pb2

import sawtooth_signing.secp256k1_signer as signing

from sawtooth_supplychain.supplychain_exceptions import SupplyChainException

import sawtooth_supplychain.addressing as addressing
import sawtooth_supplychain.time_utils as time_utils

LOGGER = logging.getLogger(__name__)


def create_batch(transactions, private_key, public_key):
    transaction_signatures = [t.header_signature for t in transactions]

    header = batch_pb2.BatchHeader(
        signer_pubkey=public_key,
        transaction_ids=transaction_signatures)

    header_bytes = header.SerializeToString()

    signature = signing.sign(header_bytes, private_key)

    batch = batch_pb2.Batch(
        header=header_bytes,
        transactions=transactions,
        header_signature=signature)

    return batch


class SupplyChainClient(object):
    def __init__(self, base_url, keyfile):
        self._base_url = base_url

        try:
            with open(keyfile) as fd:
                self._private_key = fd.read().strip()
                fd.close()
        except:
            raise IOError("Failed to read keys.")
        self._public_key = signing.generate_pubkey(self._private_key)

    @property
    def public_key(self):
        return self._public_key

    def _send_request(self, suffix, content=None, content_type=None):
        url = "{}/{}?wait=5".format(self._base_url, suffix)
        LOGGER.debug("Submit request to %s", url)
        if content_type is not None:
            content_type = {'Content-Type': content_type}

        if content is None or content_type is None:
            request = urllib.request.Request(url)
        else:
            request = urllib.request.Request(url, content, content_type)
        try:
            result = urllib.request.urlopen(request).read().decode()
        except BaseException as err:
            LOGGER.error("Exception in _send_request %s", url)
            raise SupplyChainException(err)
        return result

    def update_record(self, update, addresses):
        update['MessageType'] = 'Record'
        update['Timestamp'] = time.time()
        LOGGER.info("update_record message")
        LOGGER.info(update)

        # Add addresses for agents this txn might touch
        result = self.sendtxn(update, addresses, addresses)
        if result is None:
            raise SupplyChainException('update_record failed!')

        # Return the record ID - if it's a new record we get this from
        # sendtxn, otherwise through the specified record
        result = update['record_id']

        return result

    def update_agent(self, update):
        update['MessageType'] = 'Agent'
        agent_id = addressing.get_agent_id(self._public_key)
        address = addressing.get_agent_index(agent_id)
        result = self.sendtxn(update, [address], [address])
        if result is None:
            raise SupplyChainException('update_agent failed!')
        return address

    def sendtxn(self, update, inputs, outputs):
        ret_val = None
        payload = json.dumps(update).encode()
        payload_hash = hashlib.sha512(payload).hexdigest()

        header = transaction_pb2.TransactionHeader(
            signer_pubkey=self._public_key,
            family_name='sawtooth_supplychain',
            family_version='0.5',
            inputs=inputs,
            outputs=outputs,
            dependencies=[],
            payload_encoding="application/json",
            payload_sha512=payload_hash,
            batcher_pubkey=self._public_key,
            nonce=time.time().hex().encode())

        header_bytes = header.SerializeToString()

        signature = signing.sign(header_bytes, self._private_key)

        transaction = transaction_pb2.Transaction(
            header=header_bytes,
            payload=payload,
            header_signature=signature)

        batch = create_batch(transactions=[transaction],
                             private_key=self._private_key,
                             public_key=self._public_key)

        batch_list = batch_pb2.BatchList(batches=[batch])

        result = self._send_request(
            "batches", batch_list.SerializeToString(),
            'application/octet-stream')

        if ret_val is None:
            ret_val = result

        return ret_val

    # Get the state from the blockchain and format it into a dictionary.
    # Note this is pretty inefficient to do every time - should come up
    # with a better way to get this down the road.
    def fetch_state(self):
        state = json.loads(self._send_request("state"))
        address_map = {}
        for entry in state['data']:
            address_map[entry['address']] = entry['data']
        return address_map

    def get_history(self, record_id, time_zone):
        # { Dates : [ <Day>+ ] }
        # <Day> = { Day: "date", values: [ <value>+ ] }
        # <value> = { Time: "", Holder: "", Record: "",
        #             Location: { Lat: "", Long: "", Name: "" },
        #             Temp: { AVG: "", MIN: "", MAX: "" }
        #           }
        self._current_state.fetch()
        store = self._current_state.state
        assert store is not None
        history = RecordHistory(self, store, record_id, time_zone)
        return history.generate()

    def get_record_list(self, time_zone):
        state = self.fetch_state()
        assert state is not None
        record_list = RecordList(self, state, time_zone)
        return record_list.generate()

    def get_agent_list(self):
        state = self.fetch_state()
        assert state is not None
        agent_list = AgentList(self, state)
        return agent_list.generate()


def decode_json(data):
    return json.loads(base64.b64decode(data).decode())


class RecordHistory(object):
    def __init__(self, client, store, record_id, time_zone):
        self.client = client
        self.store = store
        self.record_id = record_id
        self.time_zone = time_zone

    def record_store(self, identifier):
        return "Record." + id

    def agent_store(self, identifier):
        return "Agent." + id

    def generate(self):
        # Find the record store
        record = self.store.get(self.record_store(self.record_id))
        if record is None:
            raise SupplyChainException('record ID {} not found'.format(
                self.record_id))

        # Generate the record history
        history = self.gen_record(self.record_id)

        return history

    def gen_record(self, record_id):
        # Recurse through the parents. For multiple parents for now just
        # merge the records. TBD: Think about how we want to display
        # multiple parents and children.

        # Find the record store
        record = self.store.get(self.record_store(record_id))

        # Get the current record day
        record_day = self.gen_record_day(record_id, record)

        # Create a list of dates
        dates = [record_day]

        if record['RecordInfo']['Parents'] is not None:
            for parent_id in record['RecordInfo']['Parents']:
                # Get the parent history
                parent_history = self.gen_record(parent_id)

                # Merge it in
                if parent_history[0]['Day'] == record_day['Day']:
                    # Same day, so just merge the Day values lists
                    record_day['values'].extend(parent_history[0]['values'])
                else:
                    # Different days so extend the dates list
                    dates.extend(parent_history)

        return dates

    def gen_record_day(self, record_id, record):
        day = {}

        record_info = record['RecordInfo']
        seconds = float(record_info['Timestamp'])
        if self.time_zone is not None:
            seconds -= int(self.time_zone) * 60
        record_time = time.gmtime(seconds)

        # Generate the date string
        day['Day'] = time.strftime("%b %d, %Y - %A", record_time)

        # Insert the value
        value = {}
        day['values'] = [value]

        # Populate value
        value['Time'] = time_utils.secs_to_time(record_info['Timestamp'],
                                                self.time_zone)

        agent = self.store.get(self.agent_store(record_info['CurrentHolder']))
        value['Holder'] = record_info['CurrentHolder']
        value['HolderName'] = agent['Name']

        value['Record'] = record_id

        record_telemetry = record['StoredTelemetry']
        if 'Location' in record_telemetry and \
           'Lat' in record_telemetry['Location'] and \
           record_telemetry['Location']['Lat'] != 'Unknown':
            value['Location'] = record_telemetry['Location']
        else:
            value['Location'] = {'Lat': "U",
                                 'Long': "U"}

        if 'Temperature' in record_telemetry:
            value['Temp'] = record_telemetry['Temperature']

        return day


class RecordList(object):
    def __init__(self, client, state, time_zone):
        self.client = client
        self.state = state
        self.time_zone = time_zone

    def generate(self):
        # Iterate through state and create a list of records
        records = []
        for item in self.state:
            if addressing.decode_offset(item) == 'Record':
                records.append(self.gen_record(item))
        # Sort based on timestamp, newest to oldest
        records = sorted(records, key=lambda x: x['Timestamp'], reverse=True)
        return records

    def gen_record(self, record):
        record_state = decode_json(self.state[record])
        val = {}
        val['ID'] = record

        val['Date'] = time_utils.secs_to_datetime(
            record_state['RecordInfo']['Timestamp'],
            self.time_zone)
        val['Timestamp'] = record_state['RecordInfo']['Timestamp']

        owner_idx = record_state['RecordInfo']['Owner']
        val['Owner'] = record_state['RecordInfo']['Owner']
        val['OwnerName'] = decode_json(self.state[owner_idx])['Name']

        holder_idx = record_state['RecordInfo']['CurrentHolder']
        val['Holder'] = record_state['RecordInfo']['CurrentHolder']
        val['HolderName'] = decode_json(self.state[holder_idx])['Name']
        return val


class AgentList(object):
    def __init__(self, client, state):
        self.client = client
        self.state = state

    def generate(self):
        # Iterate through state and create a list of agents
        agents = []
        for item in self.state:
            if addressing.decode_offset(item) == 'Agent':
                agents.append(self.gen_agent(item))
        # Sort based on name
        agents = sorted(agents, key=lambda x: x['Name'])
        return agents

    def gen_agent(self, agent):
        agent_state = decode_json(self.state[agent])
        val = {}
        val['ID'] = agent

        val['Name'] = agent_state['Name']
        val['Type'] = agent_state['Type']
        if 'Url' in agent_state and agent_state['Url']:
            val['Url'] = agent_state['Url']
        else:
            val['Url'] = ""
        return val
