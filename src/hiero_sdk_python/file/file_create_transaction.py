from __future__ import annotations

import time

from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.crypto.key import Key
from hiero_sdk_python.crypto.key_list import KeyList
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.hapi.services import (
    basic_types_pb2,
    file_create_pb2,
    transaction_pb2,
)
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.timestamp import Timestamp
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.utils.file_utils import encode_file_contents
from hiero_sdk_python.utils.key_utils import normalize_keys


class FileCreateTransaction(Transaction):
    """
    Represents a file create transaction on the network.

    This transaction creates a new file on the network with the specified keys, contents,
    expiration time and memo.

    Inherits from the base Transaction class and implements the required methods
    to build and execute a file create transaction.
    """

    # 90 days in seconds is the default expiration time
    DEFAULT_EXPIRY_SECONDS = 90 * 24 * 60 * 60  # 7776000

    def __init__(
        self,
        keys: list[Key] | None = None,
        contents: str | bytes | None = None,
        expiration_time: Timestamp | None = None,
        file_memo: str | None = None,
    ):
        """
        Initializes a new FileCreateTransaction instance with the specified parameters.

        Args:
            keys (Optional[list[Key]], optional): The keys that are allowed to update/delete the file.
            contents (Optional[str | bytes], optional): The contents of the file to create. Strings will be automatically encoded as UTF-8 bytes.
            expiration_time (Optional[Timestamp], optional): The time at which the file should expire.
            file_memo (Optional[str], optional): A memo to include with the file.
        """
        super().__init__()
        self.keys: list[Key] = normalize_keys(keys) or []
        self.contents: bytes | None = encode_file_contents(contents)
        self.expiration_time: Timestamp | None = (
            expiration_time if expiration_time else Timestamp(int(time.time()) + self.DEFAULT_EXPIRY_SECONDS, 0)
        )
        self.file_memo: str | None = file_memo
        self._default_transaction_fee = Hbar(5).to_tinybars()

    def set_keys(self, keys: list[Key] | None | Key) -> FileCreateTransaction:
        """
        Sets the keys for this file create transaction.

        Args:
            keys (list[Key] | Key | None): The keys to set for the file. Can be a
                list of Key objects (e.g. PublicKey, PrivateKey, KeyList), a single
                Key, or None. None and an empty list are equivalent for file
                creation: the file is created without keys and is immutable.

        Returns:
            FileCreateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.keys = normalize_keys(keys) or []
        return self

    def set_contents(self, contents: str | bytes | bytearray | None) -> FileCreateTransaction:
        """
        Sets the contents for this file create transaction.

        Args:
            contents (str | bytes | bytearray | None): The contents of the file to create.
                Strings will be automatically encoded as UTF-8 bytes.

        Returns:
            FileCreateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.contents = encode_file_contents(contents)
        return self

    def set_expiration_time(self, expiration_time: Timestamp | None) -> FileCreateTransaction:
        """
        Sets the expiration time for this file create transaction.

        Args:
            expiration_time (Optional[Timestamp]): The expiration time for the file.

        Returns:
            FileCreateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.expiration_time = expiration_time
        return self

    def set_file_memo(self, file_memo: str | None) -> FileCreateTransaction:
        """
        Sets the memo for this file create transaction.

        Args:
            file_memo (Optional[str]): The memo to set for the file.

        Returns:
            FileCreateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.file_memo = file_memo
        return self

    def _build_proto_body(self):
        """
        Returns the protobuf body for the file create transaction.

        Returns:
            FileCreateTransactionBody: The protobuf body for this transaction.
        """
        return file_create_pb2.FileCreateTransactionBody(
            keys=KeyList().set_keys(self.keys).to_proto(),
            contents=self.contents if self.contents is not None else b"",
            expirationTime=self.expiration_time._to_protobuf() if self.expiration_time else None,
            memo=self.file_memo if self.file_memo is not None else "",
        )

    def build_transaction_body(self):
        """
        Builds the transaction body for this file create transaction.

        Returns:
            TransactionBody: The built transaction body.
        """
        file_create_body = self._build_proto_body()
        transaction_body = self.build_base_transaction_body()
        transaction_body.fileCreate.CopyFrom(file_create_body)
        return transaction_body

    def build_scheduled_body(self) -> SchedulableTransactionBody:
        """
        Builds the scheduled transaction body for this file create transaction.

        Returns:
            SchedulableTransactionBody: The built scheduled transaction body.
        """
        file_create_body = self._build_proto_body()
        schedulable_body = self.build_base_scheduled_body()
        schedulable_body.fileCreate.CopyFrom(file_create_body)
        return schedulable_body

    def _get_method(self, channel: _Channel) -> _Method:
        """
        Gets the method to execute the file create transaction.

        This internal method returns a _Method object containing the appropriate gRPC
        function to call when executing this transaction on the Hedera network.

        Args:
            channel (_Channel): The channel containing service stubs

        Returns:
            _Method: An object containing the transaction function to create a file.
        """
        return _Method(transaction_func=channel.file.createFile, query_func=None)

    def _from_proto(self, proto: file_create_pb2.FileCreateTransactionBody) -> FileCreateTransaction:
        """
        Initializes a new FileCreateTransaction instance from a protobuf object.

        Args:
            proto (FileCreateTransactionBody): The protobuf object to initialize from.

        Returns:
            FileCreateTransaction: This transaction instance.
        """
        self.keys = KeyList.from_proto(proto.keys).keys if proto.HasField("keys") else []
        self.contents = proto.contents
        self.expiration_time = (
            Timestamp._from_protobuf(proto.expirationTime) if proto.HasField("expirationTime") else None
        )
        self.file_memo = proto.memo
        return self

    @classmethod
    def _from_protobuf(
        cls,
        transaction_body: transaction_pb2.TransactionBody,
        body_bytes: bytes,
        sig_map: basic_types_pb2.SignatureMap | None = None,
    ) -> FileCreateTransaction:
        """
        Creates a FileCreateTransaction instance from protobuf components.

        Args:
            transaction_body (TransactionBody): The parsed TransactionBody protobuf.
            body_bytes (bytes): The raw bytes of the transaction body.
            sig_map (SignatureMap, optional): The SignatureMap protobuf containing signatures.

        Returns:
            FileCreateTransaction: A new transaction instance with all fields restored.
        """
        transaction = super()._from_protobuf(transaction_body, body_bytes, sig_map)

        if transaction_body.HasField("fileCreate"):
            pb = transaction_body.fileCreate
            transaction.keys = KeyList.from_proto(pb.keys).keys if pb.HasField("keys") else []
            transaction.contents = pb.contents
            transaction.expiration_time = (
                Timestamp._from_protobuf(pb.expirationTime) if pb.HasField("expirationTime") else None
            )
            transaction.file_memo = pb.memo

        return transaction
