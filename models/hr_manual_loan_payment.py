from odoo import models, fields, api

class HrManualLoanPayment(models.Model):
    _name = 'hr.manual.loan.payment'
    _description = 'Manual Loan Payment'

    loan_line_id = fields.Many2one('hr.loan.line', string='Loan Installment', required=True,
                                   domain="[('paid', '=', False)]")
    payment_date = fields.Date(string='Payment Date', default=fields.Date.today(), required=True)
    amount = fields.Float(string='Amount', required=True)
    notes = fields.Text(string='Notes')

    def action_confirm_payment(self):
        """Confirm manual payment and mark the loan line as paid."""
        for payment in self:
            if payment.loan_line_id:
                payment.loan_line_id.write({
                    'paid': True,
                    'is_manual_payment': True,
                    'manual_payment_date': payment.payment_date,
                })
