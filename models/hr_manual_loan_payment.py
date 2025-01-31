from odoo import models, fields, api

class HrManualLoanPayment(models.Model):
    _name = 'hr.manual.loan.payment'
    _description = 'Manual Loan Payment'

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    loan_id = fields.Many2one('hr.loan', string='Loan', domain="[('employee_id', '=', employee_id)]")
    loan_line_ids = fields.Many2many('hr.loan.line', string='Loan Installments',
                                     domain="[('loan_id', '=', loan_id), ('paid', '=', False)]")
    payment_date = fields.Date(string='Payment Date', default=fields.Date.today(), required=True)
    amount = fields.Float(string='Amount', required=True)
    notes = fields.Text(string='Notes')

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        """Reset loan_id dan loan_line_ids saat employee_id berubah."""
        self.loan_id = False
        self.loan_line_ids = False

    @api.onchange('loan_id')
    def _onchange_loan_id(self):
        """Reset loan_line_ids saat loan_id berubah."""
        self.loan_line_ids = False

    def action_confirm_payment(self):
        """Confirm manual payment and mark the selected loan lines as paid."""
        for payment in self:
            if payment.loan_line_ids:
                payment.loan_line_ids.write({
                    'paid': True,
                    'is_manual_payment': True,
                    'manual_payment_date': payment.payment_date,
                })
