from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import KeywordGroup, ScanRule
class ScanHistoryView:  
    @login_required(login_url="login_cms")
    def manage_keywords(request):
        if request.method == "POST":
            action = request.POST.get('action')
            
            # 1. Thêm Group mới
            if action == "add_group":
                name = request.POST.get('new_group_name')
                tag = request.POST.get('new_group_tag')
                if name and tag:
                    KeywordGroup.objects.create(name=name, log_tag=tag)
            
            # 2. Xóa Group
            elif action == "delete_group":
                group_id = request.POST.get('group_id')
                get_object_or_404(KeywordGroup, id=group_id).delete()

            # 3. Thêm từ khóa vào Group
            elif action == "add_keyword":
                group_id = request.POST.get('group_id')
                new_k = request.POST.get('new_keyword').strip()
                group = get_object_or_404(KeywordGroup, id=group_id)
                current_list = group.get_keyword_list()
                if new_k and new_k not in current_list:
                    current_list.append(new_k)
                    group.set_keyword_list(current_list)

            # 4. Xóa từ khóa khỏi Group
            elif action == "remove_keyword":
                group_id = request.POST.get('group_id')
                target_k = request.POST.get('keyword_value')
                group = get_object_or_404(KeywordGroup, id=group_id)
                current_list = group.get_keyword_list()
                if target_k in current_list:
                    current_list.remove(target_k)
                    group.set_keyword_list(current_list)
            
            if action == "add_rule":
                name = request.POST.get('rule_name')
                tag = request.POST.get('rule_tag')
                logic = request.POST.get('logic_type')
                group_ids = request.POST.getlist('group_ids')
                if name and group_ids:
                    rule = ScanRule.objects.create(name=name, log_tag=tag, logic_type=logic)
                    rule.keyword_groups.set(group_ids)

            # 6. Xóa Rule
            elif action == "delete_rule":
                rule_id = request.POST.get('rule_id')
                get_object_or_404(ScanRule, id=rule_id).delete()
            
            return redirect('manage-keywords')

        groups = KeywordGroup.objects.all()
        rules = ScanRule.objects.prefetch_related('keyword_groups').all()
        return render(request, 'keywords/update.html', {'groups': groups, 'rules': rules})
    
