from odoo import models, fields, api

class HrManualLoanPayment(models.Model):
    _name = 'hr.manual.loan.payment'
    _description = 'Manual Loan Payment'

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    loan_id = fields.Many2one('hr.loan', string='Loan', domain="[('employee_id', '=', employee_id)]")
    loan_line_ids = fields.Many2many('hr.loan.line', string='Loan Installments',
                                     domain="[('loan_id', '=', loan_id), ('paid', '=', False)]")
    payment_date = fields.Date(string='Payment Date', default=fields.Date.today(), required=True)
    amount = fields.Float(string='Amount', compute="_compute_amount", store=True, required=True)  # Field komputasi
    notes = fields.Text(string='Notes')

    # Field komputasi untuk menentukan visibilitas tombol Confirm Payment
    is_payment_confirmed = fields.Boolean(
        string="Is Payment Confirmed",
        compute="_compute_is_payment_confirmed",
        store=True,
        help="Field ini menentukan apakah ada loan_line yang sudah dibayar."
    )

    # Field komputasi untuk menentukan visibilitas tombol Cancel
    show_cancel_button = fields.Boolean(
        string="Show Cancel Button",
        compute="_compute_show_cancel_button",
        help="Field ini menentukan apakah tombol Cancel harus ditampilkan."
    )

    @api.depends('loan_line_ids.amount')
    def _compute_amount(self):
        """Menghitung total amount dari loan_line_ids."""
        for payment in self:
            payment.amount = sum(line.amount for line in payment.loan_line_ids)

    @api.depends('loan_line_ids.paid')
    def _compute_is_payment_confirmed(self):
        """Menghitung apakah ada loan_line yang sudah dibayar."""
        for payment in self:
            payment.is_payment_confirmed = any(line.paid for line in payment.loan_line_ids)

    @api.depends('loan_line_ids.paid')
    def _compute_show_cancel_button(self):
        """Menghitung apakah tombol Cancel harus ditampilkan."""
        for payment in self:
            payment.show_cancel_button = any(line.paid for line in payment.loan_line_ids)

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

    def action_cancel_payment(self):
        """Cancel manual payment and mark the selected loan lines as unpaid."""
        for payment in self:
            if payment.loan_line_ids:
                payment.loan_line_ids.write({
                    'paid': False,  # Mengubah status paid menjadi False
                    'is_manual_payment': False,  # Reset status manual payment
                    'manual_payment_date': False,  # Reset tanggal pembayaran manual
                })