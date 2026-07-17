p = 'attendance/urls.py'
c = open(p, encoding='utf-8').read()

new_urls = """    path('api/mobile/employee/summary/', api_employee_profile.my_summary),
    path('api/mobile/manager/employees/', api_employee_profile.manager_employees_list),
    path('api/mobile/manager/employees/<int:emp_id>/profile/', api_employee_profile.manager_employee_profile),
    path('api/mobile/manager/employees/<int:emp_id>/documents/', api_employee_profile.manager_employee_documents),
    path('api/mobile/manager/employees/<int:emp_id>/movements/', api_employee_profile.manager_employee_movements),
    path('api/mobile/manager/employees/<int:emp_id>/summary/', api_employee_profile.manager_employee_summary),
"""

anchor = 'path("api/mobile/employee/movements/", api_employee_profile.my_movements),'

if 'manager/employees' in c and 'employee/summary' in c:
    print('SKIP - already added')
elif anchor in c:
    c = c.replace(anchor, anchor + '\n' + new_urls)
    open(p, 'w', encoding='utf-8').write(c)
    print('SUCCESS - URLs added')
else:
    print('ANCHOR NOT FOUND')