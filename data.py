from flask import Flask, request, jsonify, render_template_string
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///crud.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 数据模型定义
class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data_sources_name = db.Column(db.String(100), nullable=False)
    data_sources_code = db.Column(db.String(100), nullable=False)
    abstracts = db.Column(db.String(100))
    data_range = db.Column(db.String(50))
    frequency_of_updates = db.Column(db.String(50))
    sources_format = db.Column(db.String(50))
    field = db.Column(db.String(50))
    status = db.Column(db.String(10))
    visible_range = db.Column(db.String(20))
    data_items = db.relationship('DataItem', backref='item', lazy=True, cascade="all, delete-orphan")

class DataItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    field_label_zh = db.Column(db.String(100))
    field_label_en = db.Column(db.String(100))
    field_type = db.Column(db.String(100))

# 主页面HTML模板
INDEX_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>数据管理</title>
    <style>
        body { font-family: Arial; max-width: 1200px; margin: 0 auto; padding: 20px; }
        input, button { padding: 8px; margin: 5px 0; }
        .input-container { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 20px; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        button { cursor: pointer; background-color: #007bff; color: white; border: none; padding: 5px 10px; border-radius: 3px; }
        button:hover { background-color: #0056b3; }
        .action-buttons { display: flex; gap: 5px; }
        .edit-form { display: none; margin-top: 10px; padding: 10px; background: #f5f5f5; border-radius: 5px; }
    </style>
</head>
<body>
    <h2>数据管理</h2>
    <div class="input-container">
        <input id="data_sources_name" placeholder="数据资源名称" maxlength="100">
        <input id="data_sources_code" placeholder="数据资源代码" maxlength="100">
        <input id="abstracts" placeholder="摘要信息" maxlength="100">
        <input id="data_range" placeholder="数据范围" maxlength="50">
        <input id="frequency_of_updates" placeholder="更新频率" maxlength="50">
        <input id="sources_format" placeholder="资源格式" maxlength="50">
        <input id="status" placeholder="状态" maxlength="10">
        <input id="field" placeholder="所属领域" maxlength="50">
        <input id="visible_range" placeholder="可见状态" maxlength="20">
        <button onclick="saveItem()">保存</button>
        <button onclick="searchItem()">搜索</button>
    </div>
    <table id="items">
        <tr>
            <th>序号</th>
            <th>数据资源名称</th>
            <th>数据资源代码</th>
            <th>摘要信息</th>
            <th>数据范围</th>
            <th>更新频率</th>
            <th>资源格式</th>
            <th>状态</th>
            <th>所属领域</th>
            <th>可见范围</th>
            <th>操作</th>
        </tr>
    </table>
    <script>
        let currentEditId = null;

        // 加载页面时获取所有数据
        function loadItems() {
            fetch('/items')
                .then(response => response.json())
                .then(data => {
                    const table = document.getElementById('items');
                    table.innerHTML = '<tr><th>序号</th><th>数据资源名称</th><th>数据资源代码</th><th>摘要信息</th><th>数据范围</th><th>更新频率</th><th>资源格式</th><th>状态</th><th>所属领域</th><th>可见范围</th><th>操作</th></tr>';
                    data.forEach((item, index) => {
                        const row = table.insertRow();
                        row.innerHTML = `
                            <td>${index + 1}</td>
                            <td>${item.data_sources_name}</td>
                            <td>${item.data_sources_code}</td>
                            <td>${item.abstracts || '--'}</td>
                            <td>${item.data_range || '--'}</td>
                            <td>${item.frequency_of_updates || '--'}</td>
                            <td>${item.sources_format || '--'}</td>
                            <td>${item.status || '--'}</td>
                            <td>${item.field || '--'}</td>
                            <td>${item.visible_range || '--'}</td>
                            <td class="action-buttons">
                                <button onclick="viewItem(${item.id})">查看</button>
                                <button onclick="editItem(${item.id})">编辑</button>
                                <button onclick="deleteItem(${item.id})">删除</button>
                            </td>
                        `;
                        // 添加编辑表单
                        const editRow = table.insertRow();
                        editRow.id = `edit-form-${item.id}`;
                        editRow.className = 'edit-form';
                        editRow.innerHTML = `
                            <td colspan="11">
                                <input id="edit_data_sources_name_${item.id}" value="${item.data_sources_name}" maxlength="100">
                                <input id="edit_data_sources_code_${item.id}" value="${item.data_sources_code}" maxlength="100">
                                <input id="edit_abstracts_${item.id}" value="${item.abstracts || ''}" maxlength="100">
                                <input id="edit_data_range_${item.id}" value="${item.data_range || ''}" maxlength="50">
                                <input id="edit_frequency_of_updates_${item.id}" value="${item.frequency_of_updates || ''}" maxlength="50">
                                <input id="edit_sources_format_${item.id}" value="${item.sources_format || ''}" maxlength="50">
                                <input id="edit_status_${item.id}" value="${item.status || ''}" maxlength="10">
                                <input id="edit_field_${item.id}" value="${item.field || ''}" maxlength="50">
                                <input id="edit_visible_range_${item.id}" value="${item.visible_range || ''}" maxlength="20">
                                <button onclick="updateItem(${item.id})">保存</button>
                                <button onclick="hideEditForm(${item.id})">取消</button>
                            </td>
                        `;
                    });
                })
                .catch(error => console.error('加载数据失败:', error));
        }

        // 保存数据
        function saveItem() {
            const data = {
                data_sources_name: document.getElementById('data_sources_name').value,
                data_sources_code: document.getElementById('data_sources_code').value,
                abstracts: document.getElementById('abstracts').value,
                data_range: document.getElementById('data_range').value,
                frequency_of_updates: document.getElementById('frequency_of_updates').value,
                sources_format: document.getElementById('sources_format').value,
                status: document.getElementById('status').value,
                field: document.getElementById('field').value,
                visible_range: document.getElementById('visible_range').value
            };

            fetch('/items', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(err => { throw new Error(err.error || '保存失败'); });
                }
                return response.json();
            })
            .then(data => {
                alert('保存成功');
                loadItems(); // 重新加载数据
                document.querySelectorAll('.input-container input').forEach(input => input.value = '');
            })
            .catch(error => {
                console.error('保存错误:', error);
                alert('保存失败: ' + error.message);
            });
        }

        // 搜索数据
        function searchItem() {
            const params = new URLSearchParams();
            const fields = ['data_sources_name', 'data_sources_code', 'abstracts', 'data_range', 
                          'frequency_of_updates', 'sources_format', 'status', 'field', 'visible_range'];

            fields.forEach(field => {
                const value = document.getElementById(field).value;
                if (value) params.append(field, value);
            });

            fetch(`/items/search?${params.toString()}`)
                .then(response => response.json())
                .then(data => {
                    const table = document.getElementById('items');
                    table.innerHTML = '<tr><th>序号</th><th>数据资源名称</th><th>数据资源代码</th><th>摘要信息</th><th>数据范围</th><th>更新频率</th><th>资源格式</th><th>状态</th><th>所属领域</th><th>可见范围</th><th>操作</th></tr>';
                    data.forEach((item, index) => {
                        const row = table.insertRow();
                        row.innerHTML = `
                            <td>${index + 1}</td>
                            <td>${item.data_sources_name}</td>
                            <td>${item.data_sources_code}</td>
                            <td>${item.abstracts || '--'}</td>
                            <td>${item.data_range || '--'}</td>
                            <td>${item.frequency_of_updates || '--'}</td>
                            <td>${item.sources_format || '--'}</td>
                            <td>${item.status || '--'}</td>
                            <td>${item.field || '--'}</td>
                            <td>${item.visible_range || '--'}</td>
                            <td class="action-buttons">
                                <button onclick="viewItem(${item.id})">查看</button>
                                <button onclick="editItem(${item.id})">编辑</button>
                                <button onclick="deleteItem(${item.id})">删除</button>
                            </td>
                        `;
                        const editRow = table.insertRow();
                        editRow.id = `edit-form-${item.id}`;
                        editRow.className = 'edit-form';
                        editRow.innerHTML = `
                            <td colspan="11">
                                <input id="edit_data_sources_name_${item.id}" value="${item.data_sources_name}" maxlength="100">
                                <input id="edit_data_sources_code_${item.id}" value="${item.data_sources_code}" maxlength="100">
                                <input id="edit_abstracts_${item.id}" value="${item.abstracts || ''}" maxlength="100">
                                <input id="edit_data_range_${item.id}" value="${item.data_range || ''}" maxlength="50">
                                <input id="edit_frequency_of_updates_${item.id}" value="${item.frequency_of_updates || ''}" maxlength="50">
                                <input id="edit_sources_format_${item.id}" value="${item.sources_format || ''}" maxlength="50">
                                <input id="edit_status_${item.id}" value="${item.status || ''}" maxlength="10">
                                <input id="edit_field_${item.id}" value="${item.field || ''}" maxlength="50">
                                <input id="edit_visible_range_${item.id}" value="${item.visible_range || ''}" maxlength="20">
                                <button onclick="updateItem(${item.id})">保存</button>
                                <button onclick="hideEditForm(${item.id})">取消</button>
                            </td>
                        `;
                    });
                })
                .catch(error => console.error('搜索失败:', error));
        }

        // 查看详情
        function viewItem(id) {
            window.location.href = `/items/view/${id}`;
        }

        // 编辑数据
        function editItem(id) {
            if (currentEditId && currentEditId !== id) {
                hideEditForm(currentEditId);
            }
            document.getElementById(`edit-form-${id}`).style.display = 'block';
            currentEditId = id;
        }

        // 隐藏编辑表单
        function hideEditForm(id) {
            document.getElementById(`edit-form-${id}`).style.display = 'none';
            currentEditId = null;
        }

        // 更新数据
        function updateItem(id) {
            const data = {
                data_sources_name: document.getElementById(`edit_data_sources_name_${id}`).value,
                data_sources_code: document.getElementById(`edit_data_sources_code_${id}`).value,
                abstracts: document.getElementById(`edit_abstracts_${id}`).value,
                data_range: document.getElementById(`edit_data_range_${id}`).value,
                frequency_of_updates: document.getElementById(`edit_frequency_of_updates_${id}`).value,
                sources_format: document.getElementById(`edit_sources_format_${id}`).value,
                status: document.getElementById(`edit_status_${id}`).value,
                field: document.getElementById(`edit_field_${id}`).value,
                visible_range: document.getElementById(`edit_visible_range_${id}`).value
            };

            fetch(`/items/${id}`, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(err => { throw new Error(err.error || '更新失败'); });
                }
                return response.json();
            })
            .then(data => {
                alert('更新成功');
                hideEditForm(id);
                loadItems();
            })
            .catch(error => {
                console.error('更新错误:', error);
                alert('更新失败: ' + error.message);
            });
        }

        // 删除数据
        function deleteItem(id) {
            if (confirm('确定删除此项吗？')) {
                fetch(`/items/${id}`, {
                    method: 'DELETE'
                })
                .then(response => {
                    if (!response.ok) {
                        return response.json().then(err => { throw new Error(err.error || '删除失败'); });
                    }
                    return response.json();
                })
                .then(data => {
                    alert('删除成功');
                    loadItems();
                })
                .catch(error => {
                    console.error('删除错误:', error);
                    alert('删除失败: ' + error.message);
                });
            }
        }

        // 页面加载时调用
        window.onload = loadItems;
    </script>
</body>
</html>
"""

VIEW_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>数据详情</title>
    <style>
        body { font-family: Arial; max-width: 1200px; margin: 0 auto; padding: 20px; }
        h2 { margin-bottom: 20px; }
        .section { margin-bottom: 30px; }
        .section-title { font-weight: bold; margin-bottom: 10px; }
        .info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
        .info-item { display: flex; align-items: center; }
        .info-item label { width: 120px; font-weight: bold; }
        .info-item span { flex: 1; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        button { padding: 8px 16px; background-color: #007bff; color: white; border: none; border-radius: 3px; cursor: pointer; }
        button:hover { background-color: #0056b3; }
        .data-item-form { display:none; margin:10px 0; background:#f5f5f5; padding:15px; border-radius:5px; }
        .form-grid { display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-bottom:10px; }
        .form-actions { text-align:right; margin-top:10px; }
    </style>
</head>
<body>
    <h2>数据详情</h2>

    <div class="section">
        <div class="section-title">数据资源信息</div>
        <div class="info-grid">
            <div class="info-item">
                <label>数据资源名称:</label>
                <span>{{ item.data_sources_name }}</span>
            </div>
            <div class="info-item">
                <label>数据资源代码:</label>
                <span>{{ item.data_sources_code }}</span>
            </div>
            <div class="info-item">
                <label>摘要信息:</label>
                <span>{{ item.abstracts or '--' }}</span>
            </div>
            <div class="info-item">
                <label>数据范围:</label>
                <span>{{ item.data_range or '--' }}</span>
            </div>
            <div class="info-item">
                <label>更新频率:</label>
                <span>{{ item.frequency_of_updates or '--' }}</span>
            </div>
            <div class="info-item">
                <label>资源格式:</label>
                <span>{{ item.sources_format or '--' }}</span>
            </div>
            <div class="info-item">
                <label>所属领域:</label>
                <span>{{ item.field or '--' }}</span>
            </div>
            <div class="info-item">
                <label>状态:</label>
                <span>{{ item.status or '--' }}</span>
            </div>
            <div class="info-item">
                <label>可见范围:</label>
                <span>{{ item.visible_range or '--' }}</span>
            </div>
        </div>
    </div>

    <div class="section">
        <div class="section-title">数据项管理
            <button onclick="showDataItemForm()">添加数据项</button>
        </div>

        <div id="dataItemForm" class="data-item-form">
            <div class="form-grid">
                <div>
                    <label>字段中文名:</label>
                    <input id="di_label_zh" style="width:100%">
                </div>
                <div>
                    <label>字段英文名:</label>
                    <input id="di_label_en" style="width:100%">
                </div>
                <div>
                    <label>字段类型:</label>
                    <select id="di_type" style="width:100%">
                        <option value="text">文本</option>
                        <option value="number">数字</option>
                        <option value="date">日期</option>
                        <option value="boolean">布尔值</option>
                    </select>
                </div>
            </div>
            <div class="form-actions">
                <button onclick="saveDataItem()">保存</button>
                <button onclick="hideDataItemForm()">取消</button>
            </div>
        </div>

        <table>
            <tr>
                <th>序号</th>
                <th>字段中文名</th>
                <th>字段英文名</th>
                <th>类型</th>
                <th>操作</th>
            </tr>
            {% for di in item.data_items %}
            <tr>
                <td>{{ loop.index }}</td>
                <td>{{ di.field_label_zh or '--' }}</td>
                <td>{{ di.field_label_en or '--' }}</td>
                <td>{{ di.field_type or '--' }}</td>
                <td>
                    <button onclick="editDataItem({{ di.id }})">编辑</button>
                    <button onclick="deleteDataItem({{ di.id }})">删除</button>
                </td>
            </tr>
            {% else %}
            <tr><td colspan="5" style="text-align:center;">暂无数据项</td></tr>
            {% endfor %}
        </table>
    </div>

    <button onclick="window.location.href='/'">返回</button>

    <script>
    let currentEditId = null;

    function showDataItemForm() {
        currentEditId = null;
        document.getElementById('di_label_zh').value = '';
        document.getElementById('di_label_en').value = '';
        document.getElementById('di_type').value = 'text';
        document.getElementById('dataItemForm').style.display = 'block';
    }

    function hideDataItemForm() {
        document.getElementById('dataItemForm').style.display = 'none';
    }

    function saveDataItem() {
        const itemId = {{ item.id }};
        const url = currentEditId 
            ? `/data-items/${currentEditId}` 
            : `/items/${itemId}/data-items`;

        const method = currentEditId ? 'PUT' : 'POST';

        fetch(url, {
            method: method,
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                field_label_zh: document.getElementById('di_label_zh').value,
                field_label_en: document.getElementById('di_label_en').value,
                field_type: document.getElementById('di_type').value
            })
        }).then(response => {
            if(response.ok) {
                location.reload();
            } else {
                alert('操作失败');
            }
        }).catch(error => {
            console.error('Error:', error);
            alert('操作失败');
        });
    }

    function editDataItem(id) {
        fetch(`/data-items/${id}`)
            .then(r => r.json())
            .then(data => {
                currentEditId = id;
                document.getElementById('di_label_zh').value = data.field_label_zh || '';
                document.getElementById('di_label_en').value = data.field_label_en || '';
                document.getElementById('di_type').value = data.field_type || 'text';
                document.getElementById('dataItemForm').style.display = 'block';
            });
    }

    function deleteDataItem(id) {
        if(confirm('确定删除此数据项？')) {
            fetch(`/data-items/${id}`, {method: 'DELETE'})
                .then(() => location.reload())
                .catch(error => {
                    console.error('Error:', error);
                    alert('删除失败');
                });
        }
    }
    </script>
</body>
</html>
"""

# 主数据(Item)路由
@app.route('/items', methods=['GET'])
def get_all_items():
    """获取所有主数据项"""
    try:
        items = Item.query.all()
        return jsonify([{
            'id': item.id,
            'data_sources_name': item.data_sources_name,
            'data_sources_code': item.data_sources_code,
            'abstracts': item.abstracts,
            'data_range': item.data_range,
            'frequency_of_updates': item.frequency_of_updates,
            'sources_format': item.sources_format,
            'status': item.status,
            'field': item.field,
            'visible_range': item.visible_range,
            'data_items_count': len(item.data_items)
        } for item in items])
    except Exception as e:
        print(f"Error in get_all_items: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/items/search', methods=['GET'])
def search_items():
    try:
        query = Item.query
        filters = {
            'data_sources_name': Item.data_sources_name == request.args.get('data_sources_name'),
            'data_sources_code': Item.data_sources_code == request.args.get('data_sources_code'),
            # 'abstracts': Item.abstracts == request.args.get('abstracts'),
            # 'status': Item.status == request.args.get('status')
        }

        query = query.filter(*[cond for cond in filters.values() if cond.right.value is not None])

        items = query.all()
        return jsonify([{
            'id': item.id,
            'data_sources_name': item.data_sources_name,
            'data_sources_code': item.data_sources_code,
            'abstracts': item.abstracts,
            'data_range': item.data_range,
            'frequency_of_updates': item.frequency_of_updates,
            'sources_format': item.sources_format,
            'status': item.status,
            'field': item.field,
            'visible_range': item.visible_range
        } for item in items])
    except Exception as e:
        print(f"Error in search_items: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/items/<int:item_id>', methods=['GET'])
def get_item(item_id):
    """获取单个主数据项详情"""
    try:
        item = Item.query.get_or_404(item_id)
        return jsonify({
            'id': item.id,
            'data_sources_name': item.data_sources_name,
            'data_sources_code': item.data_sources_code,
            'abstracts': item.abstracts,
            'data_range': item.data_range,
            'frequency_of_updates': item.frequency_of_updates,
            'sources_format': item.sources_format,
            'status': item.status,
            'field': item.field,
            'visible_range': item.visible_range,
            'data_items': [{
                'id': di.id,
                'field_label_zh': di.field_label_zh,
                'field_label_en': di.field_label_en,
                'field_type': di.field_type,
            } for di in item.data_items]
        })
    except Exception as e:
        print(f"Error in get_item: {str(e)}")
        return jsonify({'error': str(e)}), 404

@app.route('/items', methods=['POST'])
def create_item():
    """创建主数据项"""
    try:
        data = request.json
        print(f"Received data: {data}")

        if not data.get('data_sources_name'):
            return jsonify({'error': 'data_sources_name is required'}), 400
        if not data.get('data_sources_code'):
            return jsonify({'error': 'data_sources_code is required'}), 400

        item = Item(
            data_sources_name=data['data_sources_name'],
            data_sources_code=data['data_sources_code'],
            abstracts=data.get('abstracts'),
            data_range=data.get('data_range'),
            frequency_of_updates=data.get('frequency_of_updates'),
            sources_format=data.get('sources_format'),
            status=data.get('status', 'active'),
            field=data.get('field'),
            visible_range=data.get('visible_range', 'public')
        )
        db.session.add(item)
        db.session.commit()
        print(f"Item saved with ID: {item.id}")

        return jsonify({
            'id': item.id,
            'status': 'created',
            'data_items_count': len(item.data_items)
        }), 201
    except Exception as e:
        db.session.rollback()
        print(f"Error in create_item: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/items/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    """更新主数据项"""
    try:
        item = Item.query.get_or_404(item_id)
        data = request.json
        print(f"Updating item {item_id} with data: {data}")

        if 'data_sources_name' in data:
            item.data_sources_name = data['data_sources_name']
        if 'data_sources_code' in data:
            item.data_sources_code = data['data_sources_code']
        item.abstracts = data.get('abstracts', item.abstracts)
        item.data_range = data.get('data_range', item.data_range)
        item.frequency_of_updates = data.get('frequency_of_updates', item.frequency_of_updates)
        item.sources_format = data.get('sources_format', item.sources_format)
        item.status = data.get('status', item.status)
        item.field = data.get('field', item.field)
        item.visible_range = data.get('visible_range', item.visible_range)
        db.session.commit()
        print(f"Item {item_id} updated successfully")
        return jsonify({'status': 'updated', 'item_id': item_id})
    except Exception as e:
        db.session.rollback()
        print(f"Error in update_item: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    """删除主数据项"""
    try:
        item = Item.query.get_or_404(item_id)
        db.session.delete(item)
        db.session.commit()
        print(f"Item {item_id} deleted successfully")
        return jsonify({'status': 'deleted', 'item_id': item_id})
    except Exception as e:
        db.session.rollback()
        print(f"Error in delete_item: {str(e)}")
        return jsonify({'error': str(e)}), 500

# 数据项(DataItem)路由
@app.route('/items/<int:item_id>/data-items', methods=['GET'])
def get_all_data_items(item_id):
    """获取某个主数据项的所有数据项"""
    try:
        item = Item.query.get_or_404(item_id)
        data_items = [{
            'id': di.id,
            'field_label_zh': di.field_label_zh,
            'field_label_en': di.field_label_en,
            'field_type': di.field_type,
        } for di in item.data_items]
        return jsonify(data_items)
    except Exception as e:
        print(f"Error in get_all_data_items: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/items/<int:item_id>/data-items', methods=['POST'])
def create_data_item(item_id):
    """为某个主数据项创建数据项"""
    try:
        item = Item.query.get_or_404(item_id)
        data = request.json
        if not data.get('field_label_zh'):
            return jsonify({'error': 'field_label_zh is required'}), 400
        data_item = DataItem(
            field_label_zh=data['field_label_zh'],
            field_label_en=data.get('field_label_en'),
            field_type=data.get('field_type', 'text'),
            item=item
        )
        db.session.add(data_item)
        db.session.commit()
        return jsonify({
            'id': data_item.id,
            'item_id': item_id,
            'status': 'created'
        }), 201
    except Exception as e:
        db.session.rollback()
        print(f"Error in create_data_item: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/data-items/<int:data_item_id>', methods=['GET'])
def get_data_item(data_item_id):
    """获取单个数据项详情"""
    try:
        data_item = DataItem.query.get_or_404(data_item_id)
        return jsonify({
            'id': data_item.id,
            'item_id': data_item.item_id,
            'field_label_zh': data_item.field_label_zh,
            'field_label_en': data_item.field_label_en,
            'field_type': data_item.field_type,
        })
    except Exception as e:
        print(f"Error in get_data_item: {str(e)}")
        return jsonify({'error': str(e)}), 404

@app.route('/data-items/<int:data_item_id>', methods=['PUT'])
def update_data_item(data_item_id):
    """更新数据项"""
    try:
        data_item = DataItem.query.get_or_404(data_item_id)
        data = request.json
        if 'field_label_zh' in data:
            data_item.field_label_zh = data['field_label_zh']
        if 'field_label_en' in data:
            data_item.field_label_en = data['field_label_en']
        if 'field_type' in data:
            data_item.field_type = data['field_type']
        db.session.commit()
        return jsonify({'status': 'updated', 'data_item_id': data_item_id})
    except Exception as e:
        db.session.rollback()
        print(f"Error in update_data_item: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/data-items/<int:data_item_id>', methods=['DELETE'])
def delete_data_item(data_item_id):
    """删除数据项"""
    try:
        data_item = DataItem.query.get_or_404(data_item_id)
        db.session.delete(data_item)
        db.session.commit()
        return jsonify({'status': 'deleted', 'data_item_id': data_item_id})
    except Exception as e:
        db.session.rollback()
        print(f"Error in delete_data_item: {str(e)}")
        return jsonify({'error': str(e)}), 500

# 前端页面路由
@app.route('/')
def index():
    """前端主页面"""
    return render_template_string(INDEX_HTML)

@app.route('/items/view/<int:item_id>')
def view_item_page(item_id):
    """查看数据项详情页面"""
    item = Item.query.get_or_404(item_id)
    return render_template_string(VIEW_HTML, item=item)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        inspector = inspect(db.engine)
        print("Database tables created:", inspector.get_table_names())
    app.run(debug=True)