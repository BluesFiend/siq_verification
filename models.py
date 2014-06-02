import datetime
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Float
from sqlalchemy import Date
from sqlalchemy import DateTime
from sqlalchemy import UniqueConstraint
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class AgentNotFoundError(Exception):
    pass


class Sale(Base):
    __tablename__ = 'sale'
    id = Column(Integer, primary_key=True)
    agent_id = Column(Integer, ForeignKey('agent.id'), nullable=False)
    agent = relationship('Agent')
    postal_suburb = Column(String(100))
    annual_consumption = Column(Float, nullable=True)
    signed_date = Column(Date, nullable=True)
    loaded_date = Column(Date, nullable=True)
    client_name = Column(String(255))
    site_id = Column(String(100))
    phone_no = Column(String(20))
    channel_name = Column(String(30))
    party_code = Column(String(20))
    client_type = Column(String(20))
    district_code = Column(String(20))
    nmi_mirn = Column(String(20), unique=True)
    product_type_code = Column(String(20))
    commission_value = Column(Float, nullable=True)
    clawback_value = Column(Float, nullable=True)
    sale_status = Column(String(20))
    sale_status_histories = relationship("SaleStatusHistory", backref='sale')

    def __init__(self, agent_name=None, commission_value=None, postal_suburb=None, annual_consumption=None,
                 signed_date=None, loaded_date=None, client_name=None, site_id=None, phone_no=None,
                 channel_name=None, party_code=None, client_type=None, district_code=None, nmi_mirn=None,
                 product_type_code=None, clawback_value=None, sale_status=None):

        agents = Agent.query.filter(Agent.lumo_name == agent_name)
        if agents.count():
            agent = agents.first()
            self.agent_id = agent.id
        else:
            raise AgentNotFoundError
        self.commission_value = commission_value
        self.postal_suburb = postal_suburb
        self.annual_consumption = annual_consumption
        self.signed_date = signed_date
        self.loaded_date = loaded_date
        self.client_name = client_name
        self.site_id = site_id
        self.phone_no = phone_no
        self.channel_name = channel_name
        self.party_code = party_code
        self.client_type = client_type
        self.district_code = district_code
        self.nmi_mirn = nmi_mirn
        self.product_type_code = product_type_code
        self.clawback_value = clawback_value
        self.sale_status = sale_status

    def serialize(self):
        return {
            'agent': self.agent,
            'postal_suburb': self.postal_suburb,
            'annual_consumption': self.annual_consumption,
            'signed_date': self.signed_date,
            'loaded_date': self.loaded_date,
            'client_name': self.client_name,
            'site_id': self.site_id,
            'phone_no': self.phone_no,
            'channel_name': self.channel_name,
            'party_code': self.party_code,
            'client_type': self.client_type,
            'district_code': self.district_code,
            'nmi_mirn': self.nmi_mirn,
            'product_type': self.product_type_code,
            'commission_value': self.commission_value,
            'clawback_value': self.clawback_value,
            'sale_status': self.sale_status
        }


class SaleStatusHistory(Base):
    __tablename__ = 'sale_status_history'
    id = Column(Integer, primary_key=True)
    sale_id = Column(Integer, ForeignKey('sale.id'), nullable=False)
    status = Column(String(100), nullable=False)
    created = Column(DateTime, default=datetime.datetime.now)

    def __init__(self, sale=None, status=None):
        self.sale_id = sale.id
        self.status = status


class Agent(Base):
    __tablename__ = 'agent'
    id = Column(Integer, primary_key=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    sidn = Column(String(10), unique=True)
    email = Column(String(100))
    phone = Column(String(10))
    team = Column(String(100))
    start_date = Column(Date)
    end_date = Column(Date)
    lumo_name = Column(String(255), unique=True)
    siq = Column(Boolean, default=False)

    def __init__(self, first_name=None, last_name=None, sidn=None, email=None, phone=None,
                 start_date=None, end_date=None, lumo_name=None, siq=None, team=None):
        self.first_name = first_name
        self.last_name = last_name
        self.sidn = sidn
        self.email = email
        self.phone = phone
        self.start_date = start_date
        self.end_date = end_date
        self.lumo_name = lumo_name
        self.siq = siq
        self.team = team

    def __str__(self):
        return unicode(self)

    def __unicode__(self):
        return '{} {}'.format(self.first_name, self.last_name)
