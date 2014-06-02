from flask_wtf import Form
from wtforms import TextField
from wtforms import DateField
from wtforms import FloatField
from wtforms import SelectField
from wtforms.validators import DataRequired
from wtforms.validators import Email
from wtforms.validators import Optional
from wtforms.ext.sqlalchemy.fields import QuerySelectField

class SaleForm(Form):
    agent = QuerySelectField('Agent Name', validators=[DataRequired()])
    party_code = TextField('Party Code', validators=[DataRequired()])
    signed_date = DateField('Signed Date', validators=[DataRequired()])
    loaded_date = DateField('Loaded Date', validators=[DataRequired()])
    client_name = TextField('Customer Name', validators=[DataRequired()])
    site_id = TextField('Site ID', validators=[DataRequired()])
    phone_no = TextField('Phone #', validators=[DataRequired()])
    postal_suburb = TextField('Suburb', validators=[DataRequired()])
    district_code = TextField('District', validators=[DataRequired()])
    nmi_mirn = TextField('NMI/MIRN', validators=[DataRequired()])
    product_type = SelectField('Product Type',
                               validators=[DataRequired()],
                               choices=[('POWER', 'Power'),
                                        ('GAS', 'Gas')])
    client_type = TextField('Customer Type', validators=[DataRequired()])
    annual_consumption = TextField('Annual Consumption')
    channel_name = SelectField('Channel',
                               validators=[DataRequired()],
                               choices=[('SIQ - Residential (SIVR)', 'Residential'),
                                        ('SIQ - Commercial D2D (SIVD)', 'Commercial')])
    commission_value = TextField('Commission Value', validators=[DataRequired()])
    clawback_value = TextField('Clawback Value', validators=[])
    sale_status = SelectField('Sale Status',
                              validators=[DataRequired()],
                              choices=[('Unverified', 'Unverified'),
                                       ('Verified', 'Verified'),
                                       ('Cancelled', 'Cancelled'),
                                       ('Clawback', 'Clawback')])

    def validate_annual_consumption(form, field):
        if field.data:
            try:
                float(field.data)
            except TypeError:
                raise ValidationError('Annual consumption must be a number')

    def validate_clawback_value(form, field):
        if field.data:
            try:
                float(field.data)
            except TypeError:
                raise ValidationError('Clawback value must be a number')

    def validate_commission_value(form, field):
        if field.data:
            try:
                float(field.data)
            except TypeError:
                raise ValidationError('Commission value must be a number')

class SearchForm(Form):
    agent = QuerySelectField('Agent Name', allow_blank=True)
    party_code = TextField('Party Code')
    nmi_mirn = TextField('NMI/MIRN')
    channel_name = SelectField('Channel',
                               choices=[('', '------------'),
                                        ('SIQ - Residential (SIVR)', 'Residential'),
                                        ('SIQ - Commercial D2D (SIVD)', 'Commercial')])
    sale_status = SelectField('Sale Status',
                              choices=[('', '------------'),
                                       ('Unverified', 'Unverified'),
                                       ('Verified', 'Verified'),
                                       ('Cancelled', 'Cancelled'),
                                       ('Clawback', 'Clawback')])

class AgentSearchForm(Form):
    first_name = TextField('First Name')
    last_name = TextField('Last Name')
    sidn = TextField('SIDN')

class AgentForm(Form):
    first_name = TextField('First Name', validators=[DataRequired()])
    last_name = TextField('Last Name', validators=[DataRequired()])
    sidn = TextField('SIDN', validators=[DataRequired()])
    email = TextField('Email', validators=[DataRequired(), Email()])
    phone = TextField('Phone', validators=[DataRequired()])
    start_date = DateField('Start Date', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[Optional()])
    lumo_name = TextField('LUMO Name', validators=[DataRequired()])
