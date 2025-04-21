from flask import Flask, render_template, request, redirect, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import io
from openpyxl import Workbook

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///caixa.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class MovimentoCaixa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(10), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    quem = db.Column(db.String(100), nullable=False)
    motivo = db.Column(db.String(200), nullable=False)
    horario = db.Column(db.DateTime, default=datetime.now)

@app.route('/')
def index():
    movimentos = MovimentoCaixa.query.order_by(MovimentoCaixa.horario.desc()).all()
    saldo = sum(m.valor if m.tipo == 'entrada' else -m.valor for m in movimentos)
    return render_template('index.html', movimentos=movimentos, saldo=saldo)

@app.route('/novo', methods=['GET', 'POST'])
def novo_movimento():
    if request.method == 'POST':
        tipo = request.form['tipo']
        valor = float(request.form['valor'])
        quem = request.form['quem']
        motivo = request.form['motivo']
        movimento = MovimentoCaixa(tipo=tipo, valor=valor, quem=quem, motivo=motivo)
        db.session.add(movimento)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('novo.html')

@app.route('/exportar')
def exportar_excel():
    movimentos = MovimentoCaixa.query.order_by(MovimentoCaixa.horario).all()
    wb = Workbook()
    ws = wb.active
    ws.title = "Movimentações de Caixa"
    ws.append(["Tipo", "Valor", "Quem", "Motivo", "Horário"])
    for m in movimentos:
        ws.append([
            m.tipo,
            m.valor,
            m.quem,
            m.motivo,
            m.horario.strftime("%d/%m/%Y %H:%M")
        ])
    file_stream = io.BytesIO()
    wb.save(file_stream)
    file_stream.seek(0)
    return send_file(
        file_stream,
        as_attachment=True,
        download_name="movimentacoes_caixa.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    import os
port = int(os.environ.get('PORT', 5000))  # Pega a porta do Render ou usa 5000 localmente
app.run(host='0.0.0.0', port=port)
