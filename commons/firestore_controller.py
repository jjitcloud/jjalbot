import os
import time
import io
import logging
import dataclasses

from typing import List, Dict

from google.cloud import storage
from google.cloud import firestore
from google.cloud.firestore_v1.base_document import DocumentSnapshot
from google.cloud.firestore_v1.document import DocumentReference
from google.cloud.firestore_v1.collection import CollectionReference

class firestoreController:
    """
    JJal Dict spec
        document_name: str
        public_url: str
        filename: str
        content_type: str
        size: int
        user_id: str
        time_stamp: float
        is_public: bool
    """
    def __init__(self):
        self.collection_name = os.environ['GOOGLE_FIRESTORE_COLLECTION_NAME']
        self.db = firestore.Client()
        self.collection = self.db.collection(self.collection_name)

    def get_public_jjal_list(self)->List[DocumentSnapshot]:
        return self.collection.where('is_public', '==', True).get()

    def get_private_jjal_list(self)->List[DocumentSnapshot]:
        return self.collection.where('is_public', '==', False).get()

    def get_user_jjal_list(self, user_id: int)->List[DocumentSnapshot]:
        return self.collection.where('user_id', '==', user_id).get()

    def get_jjal_list(self)->List[DocumentSnapshot]:
        return self.collection.get()

    def get_public_jjal(self, document_name: str) -> DocumentSnapshot:
        docs = self.collection.where('is_public', '==', True).where('document_name', '==', document_name).get()
        if not docs:
            return None
        
        return docs[0]

    def get_private_jjal(self, document_name: str) -> DocumentSnapshot:
        docs = self.collection.where('is_public', '==', False).where('document_name', '==', document_name).get()
        if not docs:
            return None
        
        return docs[0]

    def get_user_jjal(self, user_id: int, document_name: str) -> DocumentSnapshot:
        docs = self.collection.where('user_id', '==', user_id).where('document_name', '==', document_name).get()
        if not docs:
            return None
        
        return docs[0]

    def get_jjal(self, document_name: str) -> DocumentSnapshot:
        docs = self.collection.where('document_name', '==', document_name).get()
        if not docs:
            return None
        
        return docs[0]

    def insert_jjal(self, document: Dict) -> str:
        doc_ref = self.collection.document()
        doc_ref.set(document)
        return doc_ref.id

    def delete_jjal(self, document_name: str) -> int:
        docs = self.collection.where('document_name', '==', document_name).get()
        deleted_count = 0
        for doc in docs:
            doc.reference.delete()
            deleted_count += 1
        return deleted_count

    def delete_user_jjal(self, user_id: int, document_name: str) -> int:
        docs = self.collection.where('user_id', '==', user_id).where('document_name', '==', document_name).get()
        deleted_count = 0
        for doc in docs:
            doc.reference.delete()
            deleted_count += 1
        return deleted_count

    def publish_jjal(self, id: str) -> None:
        jjal_ref = self.collection.document(id)
        jjal_ref.update({'is_public': True})
    
    def private_jjal(self, id: str) -> None:
        jjal_ref = self.collection.document(id)
        jjal_ref.update({'is_public': False})
