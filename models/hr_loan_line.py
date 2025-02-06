from odoo import models, fields, api

class HrLoanLine(models.Model):
    """ Model for managing details of loan request installments"""
    _name = "hr.loan.line"
    _description = "Installment Line"
    _order = "loan_id, date, id"  # Pastikan urutan berdasarkan loan_id, date, dan id

    date = fields.Date(string="Payment Date", required=True, help="Date of the payment")
    employee_id = fields.Many2one('hr.employee', string="Employee", help="Employee")
    amount = fields.Float(string="Amount", required=True, help="Amount")
    paid = fields.Boolean(string="Paid", help="Indicates whether the installment has been paid.")
    loan_id = fields.Many2one('hr.loan', string="Loan Ref.", help="Reference to the associated loan.")
    payslip_id = fields.Many2one('hr.payslip', string="Payslip Ref.", help="Reference to the associated payslip, if any.")
    
    # Field baru untuk pembayaran manual
    is_manual_payment = fields.Boolean(string='Manual Payment', default=False, help="Indicates whether the payment was made manually.")
    manual_payment_date = fields.Date(string='Manual Payment Date', help="Date when the manual payment was made.")

    # Field untuk nomor urut cicilan dalam satu loan_id
    sequence_number = fields.Integer(string="Installment Sequence", compute="_compute_sequence", store=True)

    @api.depends('loan_id', 'date', 'id')
    def _compute_sequence(self):
        """Menghitung nomor urut installment berdasarkan loan_id"""
        loan_groups = {}
        for record in self.search([], order="loan_id, date, id"):
            if record.loan_id.id not in loan_groups:
                loan_groups[record.loan_id.id] = 1
            else:
                loan_groups[record.loan_id.id] += 1
            record.sequence_number = loan_groups[record.loan_id.id]

