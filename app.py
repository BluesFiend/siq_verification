import arrow
import codecs
import csv
import re

from datetime import datetime

from flask import Flask
from flask import flash
from flask import make_response
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from sqlalchemy.exc import IntegrityError

from database import db_session
from forms import AgentForm
from forms import AgentSearchForm
from forms import SaleForm
from forms import SearchForm
from models import Agent
from models import Sale
from models import SaleStatusHistory

app = Flask(__name__)
app.secret_key = 'secret_key'


@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


@app.route('/', methods=['GET'])
def index():
    limit = int(request.args.get('limit', 20))
    page = int(request.args.get('page', 1))
    offset = limit * (page - 1)

    agent_name = request.args.get('agent_name')
    party_code = request.args.get('party_code')
    channel_name = request.args.get('channel_name')
    nmi_mirn = request.args.get('nmi_mirn')
    sale_status = request.args.get('sale_status')

    sales = Sale.query

    if agent_name:
        sales = sales.filter(Sale.agent_name.like('%{}%'.format(agent_name)))
    if channel_name:
        sales = sales.filter_by(channel_name=channel_name)
    if sale_status:
        sales = sales.filter_by(sale_status=sale_status)
    if party_code:
        sales = sales.filter(Sale.party_code.like('%{}%'.format(party_code)))
    if nmi_mirn:
        sales = sales.filter(Sale.nmi_mirn.like('%{}%'.format(nmi_mirn)))

    total = sales.count()
    sales = sales.limit(limit).offset(offset)

    pages = [x for x in range(1, total/limit + 2)]

    form = SearchForm(agent_name=agent_name,
                      channel_name=channel_name,
                      party_code=party_code,
                      nmi_mirn=nmi_mirn,
                      sale_status=sale_status)

    query_string = re.sub(r"/(\?)?", "", request.query_string)
    query_string = re.sub(r"page=[\d]*|", "", query_string)
    query_string = re.sub(r"^&|&$", "", query_string)

    context = {'sales': sales,
               'page': page,
               'pages': pages,
               'final_page': total/limit + 1,
               'total': total,
               'query_string': query_string,
               'form': form}

    return render_template('index.html', **context)


@app.route('/sale/<int:sale_id>', methods=['GET', 'POST'])
def sale(sale_id):
    sale = Sale.query.get(sale_id)
    
    sale_status_histories = SaleStatusHistory.query.filter_by(sale_id=sale_id).order_by(SaleStatusHistory.created.desc()).all()
    form = SaleForm(**sale.serialize())

    if form.validate_on_submit():
        sale_status = form.sale_status.data
        if sale_status != sale.sale_status:
            ssh = SaleStatusHistory(sale=sale, status=sale_status)
            db_session.add(ssh)

        form.populate_obj(sale)
        if sale.annual_consumption == '':
            sale.annual_consumption = None
        if sale.commission_value == '':
            sale.commission_value = None
        if sale.clawback_value == '':
            sale.clawback_value = None

        db_session.commit()

        return redirect(url_for('sale', sale_id=sale_id))
        

    context = {'sale': sale,
               'form': form,
               'sale_status_histories': sale_status_histories}

    return render_template('sale.html', **context)


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    file_types = [('sale', 'Sale Details'),
                  ('cancel', 'Cancels'),
                  ('clawback', 'Clawbacks')]

    if request.method=='POST':
        f = request.files['upload']

        data = _parse_file(f)
        file_type = request.form['file_type']

        if file_type == 'sale':
            for sale in data:
                s = Sale(sale_status='Unverified', **sale)
                db_session.add(s)
                try:
                    db_session.commit()
                except IntegrityError:
                    db_session.rollback()
                    flash('NMI {} has already been imported.'.format(sale['nmi_mirn']), 'danger')
                else:
                    ssh = SaleStatusHistory(sale=s, status='Unverified')
                    db_session.add(ssh)
                    db_session.commit()

        elif file_type == 'cancel':
            for sale in data:
                sales = Sale.query.filter(Sale.nmi_mirn == sale['nmi_mirn'])
                if sales.count():
                    s = sales.first()
                    if s.sale_status != 'Cancelled':
                        s.sale_status = 'Cancelled'
                        ssh = SaleStatusHistory(sale=s, status='Cancelled')
                        db_session.add(ssh)
                        db_session.commit()
                    else:
                        flash('NMI {} is already cancelled or clawed back.'.format(sale['nmi_mirn']), 'danger')

                else:
                    flash('NMI {} could not be found for cancellation.'.format(sale['nmi_mirn']), 'danger')
        
        elif file_type == 'clawback':
            for sale in data:
                sales = Sale.query.filter(Sale.nmi_mirn == sale['nmi_mirn'], Sale.clawback_value == None)
                if sales.count():
                    s = sales.first()
                    s.sale_status = 'Clawback'
                    s.clawback_value = sale['commission_value']
                    ssh = SaleStatusHistory(sale=s, status='Clawback')
                    db_session.add(ssh)
                    db_session.commit()
                else:
                    flash('NMI {} could not be found or is already clawed back.'.format(sale['nmi_mirn']), 'danger')

        return redirect(url_for('upload'))

    context = {'file_types': file_types}

    return render_template('upload.html', **context)


@app.route('/agents')
def agent_list():
    limit = int(request.args.get('limit', 20))
    page = int(request.args.get('page', 1))
    offset = limit * (page - 1)

    agents = Agent.query

    total = agents.count()
    agents = agents.limit(limit).offset(offset)

    pages = [x for x in range(1, total/limit + 2)]

    form = AgentSearchForm()

    query_string = re.sub(r"/(\?)?", "", request.query_string)
    query_string = re.sub(r"page=[\d]*|", "", query_string)
    query_string = re.sub(r"^&|&$", "", query_string)

    context = {'agents': agents,
               'page': page,
               'pages': pages,
               'final_page': total/limit + 1,
               'form': form,
               'query_string': query_string,
               'total': total}

    return render_template('agent_list.html', **context)


@app.route('/agent', methods=['GET', 'POST'])
@app.route('/agent/<int:agent_id>', methods=['GET', 'POST'])
def agent(agent_id=None):
    if agent_id is not None:
        agent = Agent.query.get(agent_id)
    else:
        agent = Agent()

    form = AgentForm(request.form, agent)

    if form.validate_on_submit():
        form.populate_obj(agent)

        if agent.id is None:
            db_session.add(agent)

        db_session.commit()

        return redirect(url_for('agent_list'))

    context = {'form': form}

    return render_template('agent.html', **context)


def _remove_bom(line):
    return line[3:] if line.startswith(codecs.BOM_UTF8) else line


def _parse_file(f):
    f = (_remove_bom(line) for line in f)

    headers = next(f)
    header_lookup = {header: i for i, header in enumerate(headers.strip().split(','))}
    
    header_keys = {}
    try:
        header_keys['key_channel_name'] = header_lookup['chnl_dep_name']
        header_keys['key_agent_name'] = header_lookup['agent_name']
        header_keys['key_party_code'] = header_lookup['party_code']
        header_keys['key_site_id'] = header_lookup['site_id']
        header_keys['key_client_name'] = header_lookup['client_name']
        header_keys['key_phone_no'] = header_lookup['phone_no']
        header_keys['key_postal_suburb'] = header_lookup['postal_suburb']
        header_keys['key_district_code'] = header_lookup['district_code']
        header_keys['key_nmi_mirn'] = header_lookup['nmi_mirn']
        header_keys['key_client_type'] = header_lookup['client_type']
        header_keys['key_product_type_code'] = header_lookup['product_type_code']
        header_keys['key_signed_date'] = header_lookup['SignedDate']
        header_keys['key_loaded_date'] = header_lookup['LoadedDate']
        header_keys['key_annual_consumption'] = header_lookup['annual_consumption']
        header_keys['key_commission_value'] = header_lookup['agent_commission_value']
    except KeyError:
        raise

    return [_serialize_row(row, header_keys) for row in csv.reader(f) if row]


def _parse_commission_value(comm_value):
    comm_value = re.sub(r"[()\$]", "", comm_value)
    return float(comm_value)


def _parse_date(date_string):
    if date_string:
        return arrow.get(date_string, "DD/MM/YYYY").datetime

    return None


def _parse_consumption(consumption):
    if consumption:
        return float(consumption)

    return None


def _serialize_row(row, header_keys):
    data = {}

    data['channel_name'] = row[header_keys['key_channel_name']]
    data['agent_name'] = row[header_keys['key_agent_name']]
    data['party_code'] = row[header_keys['key_party_code']]
    data['site_id'] = row[header_keys['key_site_id']]
    data['client_name'] = row[header_keys['key_client_name']]
    data['phone_no'] = row[header_keys['key_phone_no']]
    data['postal_suburb'] = row[header_keys['key_postal_suburb']]
    data['district_code'] = row[header_keys['key_district_code']]
    data['nmi_mirn'] = row[header_keys['key_nmi_mirn']]
    data['client_type'] = row[header_keys['key_client_type']]
    data['product_type_code'] = row[header_keys['key_product_type_code']]
    data['signed_date'] = _parse_date(row[header_keys['key_signed_date']])
    data['loaded_date'] = _parse_date(row[header_keys['key_loaded_date']])
    data['annual_consumption'] = _parse_consumption(row[header_keys['key_annual_consumption']])
    data['commission_value'] = _parse_commission_value(row[header_keys['key_commission_value']])

    return data


if __name__ == '__main__':
    from database import init_db
    init_db()
    app.run(debug=True)
