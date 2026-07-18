from employees.models import Employee


def get_visible_employees_qs(user):
    """
    الصلاحيات الحالية:
    - super_admin: كل الموظفين
    - company_admin: كل موظفي الشركة
    - hr_manager: كل موظفي الشركة (هنقيّدها لاحقاً بالمحدد له)
    - manager: نفسه + كل من تحته بشكل هرمي
    - employee: نفسه فقط
    """
    role = getattr(user, 'role', '') or ''

    if getattr(user, 'is_superuser', False) or role == 'super_admin':
        return Employee._base_manager.all()

    company = getattr(user, 'company', None)

    if role in ['company_admin', 'hr_manager']:
        if company:
            return Employee._base_manager.filter(company=company)
        return Employee._base_manager.none()

    me = Employee._base_manager.filter(user=user).first()
    if not me:
        return Employee._base_manager.none()

    if role == 'manager':
        visible_ids = {me.id}
        queue = [me.id]

        while queue:
            manager_id = queue.pop(0)
            subordinate_ids = list(
                Employee._base_manager.filter(
                    company=me.company,
                    direct_manager_id=manager_id
                ).values_list('id', flat=True)
            )
            for sid in subordinate_ids:
                if sid not in visible_ids:
                    visible_ids.add(sid)
                    queue.append(sid)

        return Employee._base_manager.filter(id__in=visible_ids)

    return Employee._base_manager.filter(id=me.id)


def can_view_employee(user, employee):
    if not employee:
        return False
    return get_visible_employees_qs(user).filter(id=employee.id).exists()
