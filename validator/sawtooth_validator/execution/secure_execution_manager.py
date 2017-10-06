

# REST events block, transaction
# REST over SSH


class SecureExecutionManager(object):
    class KeyEpoch(object):
        def __init__(self, transaction_keys, ledger_key):
            self.transaction_key_pair = transaction_keys # RSA key pair for transaction encruption
            self.ledger_key = ledger_key # AES key for encrypting ledger values

    def __init__(self):
        self.enclave_key_pair = None #
        self.epochs = []
        self.processors = {} # stores connection_id: AES_key
        self.sem_registry = {}
        self.load_sem_store()


    def load_sem_store(self):
        pass

    def save_sem_store(self):
        pass

    def genesis(self):
        # fail if epocch list is not empty

        txn_keys = None
        ledger_key = None
        self.epochs.append(self.KeyEpoch(txn_keys, ledger_key))
        self.save_store()

        batch = None
        # add txn to Update settings transaction key settings
        # add txn to Update settings key epoch

        return batch

    def new_epoch_genesis(self):
        txn_keys = None
        ledger_key = None
        self.epochs.append(self.KeyEpoch(txn_keys, ledger_key))
        self.save_store()

        # broadcast new keys

        batch = None
        # add txn to Update settings transaction key settings
        # add txn to Update settings key epoch

        return batch

    def handle_sem epoch_update(self, update):
        # preemptive seond of key to
        # validate AVR
        #add epoch
        pass

    def handle_sem_epoch_request(self, request):
        # validate AVR
        sem_epoch_response = None
        return sem_epoch_response

    def is_stp(self, connection_id):
        return connection_id in self.processors

    def register_processor(self, connection_id, request):
        session_aes_key = None

        # Verify AVR

        self.processors[connection_id] = session_aes_key
        encrypted_session_aes_key = None #
        response = {
            encrypted_session_aes_key
        }
        pass

    def unregister_processor(self, connection_id):
        del self.processors[connection_id]

    def handle_state_get_requests(self, connection_id, request):
        # Iterate the entries and encrypt the addresses
        return request

    def handle_state_get_response(self, connection_id, request):

        return request

    def handle_state_set_requests(self, connection_id, request):
        return request

    def handle_state_set_response(self, connection_id, request):
        return request

    def handle_state_delete_requests(self, connection_id, request):
        return request

    def handle_state_delete_response(self, connection_id, request):
        return request

    def handle_process_request(self, connection_id, request):
        return request

    def handle_process_response(self, connection_id, request):
        return request

