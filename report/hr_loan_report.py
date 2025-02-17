import time
from calendar import monthrange
from datetime import date

from odoo import fields, models, tools


class HrLoanReportView(models.Model):
    """Create a new model for getting monthly report"""
    _name = 'hr.loan.report'
    _auto = False

    now = date.today()
    month_day = monthrange(now.year, now.month)
    name = fields.Many2one('hr.employee', string='Employee',
                           help="Choose Employee")
    ref_number = fields.Char(sting='Loan Number', help="Loan reference number")
    date_loan = fields.Date(string='Loan Month', help="Starting Date for Report")
    date_payment = fields.Date(string='Payment Schedule', help="Ending Date for Report")
    state = fields.Selection(
        [('draft', 'Draft'), ('waiting_approval_1', 'Submitted'),
         ('approve', 'Approved'), ('refuse', 'Refused'), ('cancel', 'Canceled'),
         ], string="State", default='draft', help="The current state of the ")
    company_id = fields.Many2one('res.company', string='Company',
                                 help="Choose Company")
    department_id = fields.Many2one('hr.department',
                                    string='Department',
                                    help="Choose Hr Department")
    loan_amount = fields.Float(string="Loan Amount", required=True,
                               help="Loan amount")
    total_amount = fields.Float(string="Total Amount", store=True,
                                readonly=True, compute='_compute_total_amount',
                                help="The total amount of the loan")
    balance_amount = fields.Float(string="Balance Amount", store=True,
                                  compute='_compute_total_amount',
                                  help="""The remaining balance amount of the 
                                  loan after deducting 
                                  the total paid amount.""")
    total_paid_amount = fields.Float(string="Total Paid Amount", store=True,
                                     compute='_compute_total_amount',
                                     help="The total amount that has been "
                                          "paid towards the loan.")
    line_amount = fields.Float(string="Line Amount", store=True,
                                     compute='_compute_total_amount',
                                     help="The total amount that has been "
                                          "paid towards the loan.")
    def _select(self):
        
        select_str = """
            min(lsl.id),ls.name as ref_number,ls.id,ls.name as number, emp.id as name,dp.id as 
            department_id,jb.id as job_id,cmp.id as company_id,ls.date as date_loan,lsl.date as date_payment, 
            ls.state as state,ls.loan_amount,ls.total_amount,ls.balance_amount,lsl.amount as line_amount
            """
        return select_str

    def _from(self):
        from_str = """
                hr_loan_line lsl   
                join hr_loan ls on ls.id=lsl.loan_id
                join hr_employee emp on ls.employee_id=emp.id
                left join hr_department dp on emp.department_id=dp.id
                left join hr_job jb on emp.job_id=jb.id
                join res_company cmp on cmp.id=ls.company_id
             """
        return from_str

    def _group_by(self):
        
        group_by_str = """group by ls.name,ls.id,emp.id,dp.id,jb.id,cmp.id,
        ls.date,ls.state,lsl.amount,ls.loan_amount,ls.total_amount,ls.balance_amount,lsl.date,ls.name"""
        return group_by_str

    def init(self):
        """
            Initialize or update a database view with a SELECT statement.
        """
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as ( SELECT
                   %s
                   FROM %s
                   %s
                   )""" % (
            self._table, self._select(), self._from(), self._group_by()))
