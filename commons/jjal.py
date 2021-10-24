import dataclasses

@dataclasses.dataclass
class JJal:
     document_name: str
     public_url: str
     filename: str
     content_type: str
     size: int
     user_id:int
     time_stamp:int
     is_public: bool

"""class JJal(object):
    def __init__(self, document_name: str, public_url: str, filename: str, content_type: str, size: int, user_id: str, time_stamp:float, is_public: bool):

        self.document_name = document_name
        self.public_url = public_url
        self.filename = filename
        self.content_type = content_type
        self.size = size
        self.user_id = user_id
        self.time_stamp = time_stamp
        self.is_public = is_public

    @staticmethod
    def from_dict(source):
        jjal = JJal(source['document_name'], 
        source['public_url'], 
        source['filename'], 
        source['content_type'], 
        source['size'], 
        source['user_id'], 
        source['time_stamp'], 
        source['is_public'])

        return jjal

    def to_dict(self):
        dest = {
            'document_name': self.document_name,
            'public_url': self.public_url,
            'filename': self.filename,
            'content_type': self.content_type,
            'size': self.size,
            'user_id': self.user_id,
            'time_stamp': self.time_stamp,
            'is_public': self.is_public,
        }

        return dest

    def __repr__(self):
        return(
            f'JJal(\
                document_name={self.document_name}, \
                public_url={self.public_url}, \
                filename={self.filename}, \
                content_type={self.content_type}, \
                size={self.size},\
                user_id={self.user_id},\
                time_stamp={self.time_stamp},\
                is_public={self.is_public}\
            )'
        )
"""