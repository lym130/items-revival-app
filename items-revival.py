import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import json

# 数据库文件路径
DB_FILE = 'items_with_categories.db'

class Item:
    def __init__(self, id, name, description, address, contact_phone, contact_email, category, attributes):
        self.id = id
        self.name = name
        self.description = description
        self.address = address
        self.contact_phone = contact_phone
        self.contact_email = contact_email
        self.category = category
        self.attributes = attributes  # 扩展属性，使用字典存储

class ItemApp:
    def __init__(self, root):
        self.root = root
        self.root.title("物品复活系统")
        self.create_database()
        self.items = []
        self.deleted_items = []

        self.create_widgets()
        self.load_items()
        self.load_deleted_items()
        self.is_editing = False  # 当前是否处于编辑模式

    def create_database(self):
        """创建数据库和表"""
        with sqlite3.connect(DB_FILE, timeout=10) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    description TEXT,
                    address TEXT,
                    contact_phone TEXT,
                    contact_email TEXT,
                    category TEXT,
                    attributes TEXT
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS deleted_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    description TEXT,
                    address TEXT,
                    contact_phone TEXT,
                    contact_email TEXT,
                    category TEXT,
                    attributes TEXT
                )
            ''')
            conn.commit()

    def create_widgets(self):
        """创建主界面组件"""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        self.items_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.items_frame, text="物品列表")

        self.recovery_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.recovery_frame, text="回收站")

        self.create_items_tab()
        self.create_recovery_tab()

    def create_items_tab(self):
        """创建物品管理标签页"""
        main_frame = ttk.Frame(self.items_frame)
        main_frame.pack(fill="x", padx=5, pady=5)

        # 添加/编辑物品部分
        add_frame = ttk.LabelFrame(main_frame, text="添加/编辑物品")
        add_frame.pack(side="left", fill="both", expand=True, padx=2, pady=2)

        ttk.Label(add_frame, text="名称:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.name_entry = ttk.Entry(add_frame, width=30)
        self.name_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(add_frame, text="类别:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.category_combobox = ttk.Combobox(add_frame, values=["食品", "书籍", "工具"], state="readonly", width=28)
        self.category_combobox.grid(row=1, column=1, padx=5, pady=5)
        self.category_combobox.bind("<<ComboboxSelected>>", self.update_attributes_fields)

        ttk.Label(add_frame, text="描述:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.description_entry = ttk.Entry(add_frame, width=30)
        self.description_entry.grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(add_frame, text="地址:").grid(row=3, column=0, padx=5, pady=5, sticky="e")
        self.address_entry = ttk.Entry(add_frame, width=30)
        self.address_entry.grid(row=3, column=1, padx=5, pady=5)

        ttk.Label(add_frame, text="联系人手机:").grid(row=4, column=0, padx=5, pady=5, sticky="e")
        self.phone_entry = ttk.Entry(add_frame, width=30)
        self.phone_entry.grid(row=4, column=1, padx=5, pady=5)

        ttk.Label(add_frame, text="联系人邮箱:").grid(row=5, column=0, padx=5, pady=5, sticky="e")
        self.email_entry = ttk.Entry(add_frame, width=30)
        self.email_entry.grid(row=5, column=1, padx=5, pady=5)

        self.attributes_frame = ttk.LabelFrame(add_frame, text="扩展属性")
        self.attributes_frame.grid(row=6, column=0, columnspan=2, pady=10, sticky="ew")

        self.add_button = ttk.Button(add_frame, text="添加物品", command=self.add_item)
        self.add_button.grid(row=7, column=1, padx=5, pady=10, sticky="e")

        # 查找物品部分
        search_frame = ttk.LabelFrame(main_frame, text="查找物品")
        search_frame.pack(side="left", fill="both", expand=True, padx=2, pady=2)

        # 搜索行
        search_row = ttk.Frame(search_frame)
        search_row.pack(fill="x", padx=5, pady=5)

        # 类别选择
        ttk.Label(search_row, text="类别:").pack(side="left", padx=5, pady=5)
        self.search_category_combobox = ttk.Combobox(
            search_row,
            values=["暂不选择", "食品", "书籍", "工具"],  # 增加“暂不选择”选项
            state="readonly",
            width=25
        )
        self.search_category_combobox.pack(side="left", padx=5)
        self.search_category_combobox.set("暂不选择")  # 默认选中“暂不选择”

        # 关键词输入框
        ttk.Label(search_row, text="关键词:").pack(side="left", padx=5, pady=5)
        self.search_entry = ttk.Entry(search_row, width=60)
        self.search_entry.pack(side="left", padx=5)

        # 查找和取消按钮
        self.search_button = ttk.Button(search_row, text="查找", command=self.search_items)
        self.search_button.pack(side="left", padx=5)

        self.clear_search_button = ttk.Button(search_row, text="取消", command=self.load_items)
        self.clear_search_button.pack(side="left", padx=5)

        # 列表部分
        list_frame = ttk.Frame(search_frame)
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)

        columns = ("名称", "类别", "描述", "地址", "联系人手机", "联系人邮箱", "扩展属性")
        style = ttk.Style()
        style.configure("Treeview", rowheight=24)

        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings')
        for col in columns:
            self.tree.heading(col, text=col)
        self.tree.pack(fill="both", expand=True, side="left")
        self.tree.column("名称", width=100)
        self.tree.column("类别", width=50)
        self.tree.column("描述", width=100)
        self.tree.column("地址", width=150)
        self.tree.column("联系人手机", width=150)
        self.tree.column("联系人邮箱", width=150)
        self.tree.column("扩展属性", width=200)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        buttons_frame = ttk.Frame(search_frame)
        buttons_frame.pack(fill="x", padx=10, pady=5)

        self.delete_button = ttk.Button(buttons_frame, text="删除物品", command=self.delete_item)
        self.delete_button.pack(side="right", padx=5, pady=5)

        self.edit_button = ttk.Button(buttons_frame, text="保存编辑", command=self.save_edits)
        self.edit_button.pack(side="right", padx=5, pady=5)

        self.edit_selected_button = ttk.Button(buttons_frame, text="编辑物品", command=self.load_selected_item_for_edit)
        self.edit_selected_button.pack(side="right", padx=5, pady=5)

    def create_recovery_tab(self):
        """创建回收站标签页"""
        recovery_frame = ttk.Frame(self.recovery_frame)
        recovery_frame.pack(fill="both", expand=True, padx=10, pady=5)

        columns = ("名称", "类别", "描述", "地址", "联系人手机", "联系人邮箱", "扩展属性")
        self.recovery_tree = ttk.Treeview(recovery_frame, columns=columns, show='headings')
        for col in columns:
            self.recovery_tree.heading(col, text=col)
            self.recovery_tree.column(col, width=150)
        self.recovery_tree.pack(fill="both", expand=True, side="left")

        scrollbar = ttk.Scrollbar(recovery_frame, orient="vertical", command=self.recovery_tree.yview)
        self.recovery_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        recovery_buttons_frame = ttk.Frame(self.recovery_frame)
        recovery_buttons_frame.pack(fill="x", padx=10, pady=5)

        self.permanently_delete_button = ttk.Button(recovery_buttons_frame, text="永久删除选中物品",
                                                    command=self.permanently_delete_item)
        self.permanently_delete_button.pack(side="right", padx=5)

        self.recover_button = ttk.Button(recovery_buttons_frame, text="恢复选中物品", command=self.recover_item)
        self.recover_button.pack(side="right", padx=5)

    def load_items(self):
        """加载物品列表"""
        self.items.clear()
        self.tree.delete(*self.tree.get_children())

        with sqlite3.connect(DB_FILE, timeout=10) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM items')
            for row in cursor.fetchall():
                item = Item(row[0], row[1], row[2], row[3], row[4], row[5], row[6], json.loads(row[7]))
                self.items.append(item)

                # 按列的正确顺序插入数据
                self.tree.insert(
                    '', 'end',
                    values=(
                        item.name,  # 名称
                        item.category,  # 类别
                        item.description,  # 描述
                        item.address,  # 地址
                        item.contact_phone,  # 联系人手机
                        item.contact_email,  # 联系人邮箱
                        json.dumps(item.attributes, ensure_ascii=False)  # 扩展属性
                    )
                )

    def update_attributes_fields(self, event):
        """根据类别更新扩展属性字段"""
        for widget in self.attributes_frame.winfo_children():
            widget.destroy()

        category = self.category_combobox.get()
        if category == "食品":
            ttk.Label(self.attributes_frame, text="保质期:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
            self.expiry_entry = ttk.Entry(self.attributes_frame, width=30)
            self.expiry_entry.grid(row=0, column=1, padx=5, pady=5)

            ttk.Label(self.attributes_frame, text="数量:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
            self.quantity_entry = ttk.Entry(self.attributes_frame, width=30)
            self.quantity_entry.grid(row=1, column=1, padx=5, pady=5)

        elif category == "书籍":
            ttk.Label(self.attributes_frame, text="作者:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
            self.author_entry = ttk.Entry(self.attributes_frame, width=30)
            self.author_entry.grid(row=0, column=1, padx=5, pady=5)

            ttk.Label(self.attributes_frame, text="出版社:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
            self.publisher_entry = ttk.Entry(self.attributes_frame, width=30)
            self.publisher_entry.grid(row=1, column=1, padx=5, pady=5)

        elif category == "工具":
            ttk.Label(self.attributes_frame, text="品牌:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
            self.brand_entry = ttk.Entry(self.attributes_frame, width=30)
            self.brand_entry.grid(row=0, column=1, padx=5, pady=5)

            ttk.Label(self.attributes_frame, text="型号:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
            self.model_entry = ttk.Entry(self.attributes_frame, width=30)
            self.model_entry.grid(row=1, column=1, padx=5, pady=5)

    def add_item(self):
        """添加新物品到数据库"""
        name = self.name_entry.get().strip()
        description = self.description_entry.get().strip()
        address = self.address_entry.get().strip()
        phone = self.phone_entry.get().strip()
        email = self.email_entry.get().strip()
        category = self.category_combobox.get()

        attributes = {}
        if category == "食品":
            attributes["保质期"] = self.expiry_entry.get().strip()
            attributes["数量"] = self.quantity_entry.get().strip()
        elif category == "书籍":
            attributes["作者"] = self.author_entry.get().strip()
            attributes["出版社"] = self.publisher_entry.get().strip()
        elif category == "工具":
            attributes["品牌"] = self.brand_entry.get().strip()
            attributes["型号"] = self.model_entry.get().strip()

        if not name or not category:
            messagebox.showwarning("输入错误", "请填写必要的字段：名称和类别！")
            return

        with sqlite3.connect(DB_FILE, timeout=10) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT 1 FROM items WHERE name = ? AND category = ?', (name, category))
            if cursor.fetchone():
                messagebox.showerror("重复错误", "名称和类别相同的物品已存在，无法重复添加！")
                return

            cursor.execute('''INSERT INTO items (name, description, address, contact_phone, contact_email, category, attributes) 
                              VALUES (?, ?, ?, ?, ?, ?, ?)''',
                           (name, description, address, phone, email, category, json.dumps(attributes)))
            conn.commit()

        self.load_items()
        self.clear_entries()
        messagebox.showinfo("成功", f"物品“{name}”已添加成功。")

    def load_selected_item_for_edit(self):
        """加载选中物品到编辑框"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("编辑错误", "请选择要编辑的物品！")
            return

        item_values = self.tree.item(selected[0], 'values')
        name = item_values[0]
        category = item_values[1]

        with sqlite3.connect(DB_FILE, timeout=10) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM items WHERE name = ? AND category = ?', (name, category))
            row = cursor.fetchone()
            if row:
                item = Item(row[0], row[1], row[2], row[3], row[4], row[5], row[6], json.loads(row[7]))

                # 填充编辑框
                self.name_entry.delete(0, tk.END)
                self.name_entry.insert(0, item.name)

                self.description_entry.delete(0, tk.END)
                self.description_entry.insert(0, item.description)

                self.address_entry.delete(0, tk.END)
                self.address_entry.insert(0, item.address)

                self.phone_entry.delete(0, tk.END)
                self.phone_entry.insert(0, item.contact_phone)

                self.email_entry.delete(0, tk.END)
                self.email_entry.insert(0, item.contact_email)

                self.category_combobox.set(item.category)
                self.update_attributes_fields(None)

                if item.category == "食品":
                    self.expiry_entry.insert(0, item.attributes.get("保质期", ""))
                    self.quantity_entry.insert(0, item.attributes.get("数量", ""))
                elif item.category == "书籍":
                    self.author_entry.insert(0, item.attributes.get("作者", ""))
                    self.publisher_entry.insert(0, item.attributes.get("出版社", ""))
                elif item.category == "工具":
                    self.brand_entry.insert(0, item.attributes.get("品牌", ""))
                    self.model_entry.insert(0, item.attributes.get("型号", ""))

                # 禁用“添加物品”按钮，设置为编辑模式
                self.add_button.config(state=tk.DISABLED)
                self.is_editing = True

    def save_edits(self):
        """保存编辑后的物品"""
        name = self.name_entry.get().strip()
        description = self.description_entry.get().strip()
        address = self.address_entry.get().strip()
        phone = self.phone_entry.get().strip()
        email = self.email_entry.get().strip()
        category = self.category_combobox.get()

        attributes = {}
        if category == "食品":
            attributes["保质期"] = self.expiry_entry.get().strip()
            attributes["数量"] = self.quantity_entry.get().strip()
        elif category == "书籍":
            attributes["作者"] = self.author_entry.get().strip()
            attributes["出版社"] = self.publisher_entry.get().strip()
        elif category == "工具":
            attributes["品牌"] = self.brand_entry.get().strip()
            attributes["型号"] = self.model_entry.get().strip()

        if not name or not category:
            messagebox.showwarning("输入错误", "请填写必要的字段：名称和类别！")
            return

        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("保存错误", "未选择物品进行编辑！")
            return

        # 从表格中获取选中的物品的 ID
        selected_item = self.tree.item(selected[0], 'values')
        original_name = selected_item[0]  # 获取原始名称
        original_category = selected_item[1]  # 获取原始类别

        with sqlite3.connect(DB_FILE, timeout=10) as conn:
            cursor = conn.cursor()

            # 检查是否尝试修改为与现有其他物品相同的名称和类别
            cursor.execute('SELECT id FROM items WHERE name = ? AND category = ? AND name != ? OR category != ?',
                           (name, category, original_name, original_category))
            conflict = cursor.fetchone()
            if conflict:
                messagebox.showerror("冲突错误", "名称和类别的组合与现有物品冲突，无法保存更改！")
                return

            # 执行更新操作
            cursor.execute('''UPDATE items
                              SET name = ?, description = ?, address = ?, contact_phone = ?,
                                  contact_email = ?, category = ?, attributes = ?
                              WHERE name = ? AND category = ?''',
                           (name, description, address, phone, email, category, json.dumps(attributes),
                            original_name, original_category))
            conn.commit()

        self.load_items()
        self.clear_entries()

        # 重新启用“添加物品”按钮，退出编辑模式
        self.add_button.config(state=tk.NORMAL)
        self.is_editing = False
        messagebox.showinfo("成功", f"物品“{name}”已更新成功。")

    def search_items(self):
        """根据类别和关键词查找物品"""
        category = self.search_category_combobox.get().strip()  # 获取类别
        keyword = self.search_entry.get().strip()

        # 如果选择了“暂不选择”，将类别视为未选择
        if category == "暂不选择":
            category = None

        if not keyword and not category:
            messagebox.showwarning("输入错误", "请输入关键词或选择类别进行查找！")
            return

        # 清空现有的 TreeView 数据
        self.tree.delete(*self.tree.get_children())

        # 构建动态 SQL 查询
        query = '''
            SELECT * FROM items WHERE 
            (name LIKE ? OR 
            description LIKE ? OR 
            address LIKE ? OR 
            contact_phone LIKE ? OR 
            contact_email LIKE ? OR 
            attributes LIKE ?)
        '''
        params = [f"%{keyword}%"] * 6  # 模糊匹配关键词

        if category:  # 如果选择了类别，增加类别条件
            query += " AND category = ?"
            params.append(category)

        # 在数据库中执行查询
        with sqlite3.connect(DB_FILE, timeout=10) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            results = cursor.fetchall()

        # 显示搜索结果
        if results:
            for row in results:
                item = Item(row[0], row[1], row[2], row[3], row[4], row[5], row[6], json.loads(row[7]))
                self.tree.insert(
                    '', 'end',
                    values=(
                        item.name,
                        item.category,
                        item.description,
                        item.address,
                        item.contact_phone,
                        item.contact_email,
                        json.dumps(item.attributes, ensure_ascii=False)
                    )
                )
            messagebox.showinfo("查找完成", f"找到 {len(results)} 个匹配的物品。")
        else:
            messagebox.showinfo("查找完成", "没有找到匹配的物品。")

    def clear_entries(self):
        """清空输入框"""
        self.name_entry.delete(0, tk.END)
        self.description_entry.delete(0, tk.END)
        self.address_entry.delete(0, tk.END)
        self.phone_entry.delete(0, tk.END)
        self.email_entry.delete(0, tk.END)
        self.category_combobox.set("")
        for widget in self.attributes_frame.winfo_children():
            widget.destroy()

        # 如果处于编辑模式，退出编辑模式并启用“添加物品”按钮
        if self.is_editing:
            self.add_button.config(state=tk.NORMAL)
            self.is_editing = False

    def delete_item(self):
        """删除选中物品，将其移动到回收站"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("删除错误", "请选择要删除的物品！")
            return

        confirm = messagebox.askyesno("确认删除", "确定要删除选中的物品吗？")
        if not confirm:
            return

        with sqlite3.connect(DB_FILE, timeout=10) as conn:
            cursor = conn.cursor()
            for sel in selected:
                item_values = self.tree.item(sel, 'values')
                name = item_values[0]
                cursor.execute('SELECT * FROM items WHERE name = ?', (name,))
                item = cursor.fetchone()
                if item:
                    cursor.execute('INSERT INTO deleted_items (name, description, address, contact_phone, contact_email, category, attributes) VALUES (?, ?, ?, ?, ?, ?, ?)', item[1:])
                    cursor.execute('DELETE FROM items WHERE id = ?', (item[0],))
            conn.commit()

        self.load_items()
        self.load_deleted_items()
        messagebox.showinfo("删除成功", "选中的物品已移动到回收站。")

    def recover_item(self):
        """从回收站恢复选中的物品"""
        selected = self.recovery_tree.selection()
        if not selected:
            messagebox.showwarning("恢复错误", "请选择要恢复的物品！")
            return

        with sqlite3.connect(DB_FILE, timeout=10) as conn:
            cursor = conn.cursor()
            for sel in selected:
                item_values = self.recovery_tree.item(sel, 'values')
                name = item_values[0]
                category = item_values[1]

                # 检查是否存在名称和类别相同的物品
                cursor.execute('SELECT * FROM items WHERE name = ? AND category = ?', (name, category))
                existing_item = cursor.fetchone()

                cursor.execute('SELECT * FROM deleted_items WHERE name = ? AND category = ?', (name, category))
                deleted_item = cursor.fetchone()

                if deleted_item:
                    if existing_item:
                        # 如果已存在相同名称和类别的物品，提示用户选择是否替换
                        replace = messagebox.askyesno(
                            "重复物品",
                            f"物品“{name}”（类别：{category}）已存在于列表中，是否替换？"
                        )
                        if not replace:
                            continue  # 如果用户选择不替换，则跳过恢复该物品

                        # 如果用户选择替换，删除现有物品
                        cursor.execute('DELETE FROM items WHERE id = ?', (existing_item[0],))

                    # 恢复物品到主物品列表
                    cursor.execute(
                        'INSERT INTO items (name, description, address, contact_phone, contact_email, category, attributes) VALUES (?, ?, ?, ?, ?, ?, ?)',
                        deleted_item[1:])
                    cursor.execute('DELETE FROM deleted_items WHERE id = ?', (deleted_item[0],))
            conn.commit()

        self.load_items()
        self.load_deleted_items()
        messagebox.showinfo("恢复成功", "选中的物品已恢复。")

    def permanently_delete_item(self):
        """永久删除选中的物品"""
        selected = self.recovery_tree.selection()
        if not selected:
            messagebox.showwarning("删除错误", "请选择要永久删除的物品！")
            return

        confirm = messagebox.askyesno("确认删除", "确定要永久删除选中的物品吗？此操作无法撤销。")
        if not confirm:
            return

        with sqlite3.connect(DB_FILE, timeout=10) as conn:
            cursor = conn.cursor()
            for sel in selected:
                item_values = self.recovery_tree.item(sel, 'values')
                name = item_values[0]
                cursor.execute('SELECT * FROM deleted_items WHERE name = ?', (name,))
                item = cursor.fetchone()
                if item:
                    cursor.execute('DELETE FROM deleted_items WHERE id = ?', (item[0],))
            conn.commit()

        self.load_deleted_items()
        messagebox.showinfo("删除成功", "选中的物品已永久删除。")

    def load_deleted_items(self):
        """加载回收站物品"""
        self.deleted_items.clear()
        self.recovery_tree.delete(*self.recovery_tree.get_children())

        with sqlite3.connect(DB_FILE, timeout=10) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM deleted_items')
            for row in cursor.fetchall():
                item = Item(row[0], row[1], row[2], row[3], row[4], row[5], row[6], json.loads(row[7]))
                self.deleted_items.append(item)

                # 按列的正确顺序插入数据
                self.recovery_tree.insert(
                    '', 'end',
                    values=(
                        item.name,  # 名称
                        item.category,  # 类别
                        item.description,  # 描述
                        item.address,  # 地址
                        item.contact_phone,  # 联系人手机
                        item.contact_email,  # 联系人邮箱
                        json.dumps(item.attributes, ensure_ascii=False)  # 扩展属性
                    )
                )


if __name__ == "__main__":
    root = tk.Tk()
    app = ItemApp(root)
    root.mainloop()

