"""
入力値バリデーションモジュール
メールアドレス、パスワード、その他の入力値の検証を行います
"""

import re
from typing import List, Tuple

def validate_email(email: str) -> Tuple[bool, str]:
    """
    メールアドレスのバリデーション
    
    Returns:
        Tuple[bool, str]: (有効かどうか, エラーメッセージ)
    """
    if not email:
        return False, "メールアドレスは必須です"
    
    # 最小・最大文字数チェック
    if len(email) < 5:
        return False, "メールアドレスは5文字以上で入力してください"
    
    if len(email) > 100:
        return False, "メールアドレスは100文字以下で入力してください"
    
    # メール形式チェック（RFC 5322に準拠）
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return False, "正しいメールアドレスの形式で入力してください（例: user@example.com）"
    
    # 禁止文字チェック
    forbidden_chars = ['<', '>', '"', "'", '\\', '/', '%', '&']
    if any(char in email for char in forbidden_chars):
        return False, "メールアドレスに使用できない文字が含まれています"
    
    # 連続ドットのチェック
    if '..' in email:
        return False, "メールアドレスに連続するドット(..)は使用できません"
    
    # @マークの数チェック
    if email.count('@') != 1:
        return False, "メールアドレスには@マークを1つだけ含める必要があります"
    
    return True, ""

def validate_password(password: str) -> Tuple[bool, str]:
    """
    パスワードのバリデーション
    
    Returns:
        Tuple[bool, str]: (有効かどうか, エラーメッセージ)
    """
    if not password:
        return False, "パスワードは必須です"
    
    # 最小文字数チェック
    if len(password) < 8:
        return False, "パスワードは8文字以上で入力してください"
    
    # 最大文字数チェック
    if len(password) > 50:
        return False, "パスワードは50文字以下で入力してください"
    
    # 英数字チェック
    if not re.search(r'[a-zA-Z]', password):
        return False, "パスワードには英字を含める必要があります"
    
    if not re.search(r'[0-9]', password):
        return False, "パスワードには数字を含める必要があります"
    
    # 大文字小文字チェック
    if not re.search(r'[a-z]', password):
        return False, "パスワードには小文字を含める必要があります"
    
    if not re.search(r'[A-Z]', password):
        return False, "パスワードには大文字を含める必要があります"
    
    # よくあるパスワードのチェック
    common_passwords = [
        'password', 'password123', '12345678', 'qwerty', 'abc123',
        'admin', 'admin123', 'user123', 'test123', '11111111',
        'password1', '123456789', 'welcome', 'letmein', 'monkey'
    ]
    
    if password.lower() in common_passwords:
        return False, "このパスワードは一般的すぎます。より複雑なパスワードを設定してください"
    
    # 連続する同じ文字のチェック（3文字以上）
    for i in range(len(password) - 2):
        if password[i] == password[i+1] == password[i+2]:
            return False, "同じ文字を3文字以上連続して使用することはできません"
    
    # 連続する数字のチェック（例: 123, 234, 987, 876）
    consecutive_patterns = ['012', '123', '234', '345', '456', '567', '678', '789', '987', '876', '765', '654', '543', '432', '321', '210']
    password_lower = password.lower()
    for pattern in consecutive_patterns:
        if pattern in password_lower:
            return False, "連続する数字や文字の組み合わせは避けてください"
    
    return True, ""

def validate_name(name: str) -> Tuple[bool, str]:
    """
    名前のバリデーション
    
    Returns:
        Tuple[bool, str]: (有効かどうか, エラーメッセージ)
    """
    if not name:
        return False, "名前は必須です"
    
    # 文字数チェック
    if len(name.strip()) < 1:
        return False, "名前を入力してください"
    
    if len(name) > 50:
        return False, "名前は50文字以下で入力してください"
    
    # 空白のみの名前を禁止
    if name.strip() == "":
        return False, "名前に空白のみは使用できません"
    
    # 特殊文字のチェック（基本的な記号は許可、HTMLタグなどは禁止）
    forbidden_chars = ['<', '>', '"', "'", '\\', '/', '%', '&', '|', '*', '?', ':']
    if any(char in name for char in forbidden_chars):
        return False, "名前に使用できない文字が含まれています"
    
    return True, ""

def validate_user_input(email: str, password: str, name: str) -> Tuple[bool, List[str]]:
    """
    ユーザー入力の総合バリデーション
    
    Returns:
        Tuple[bool, List[str]]: (すべて有効かどうか, エラーメッセージのリスト)
    """
    errors = []
    
    # メールアドレスバリデーション
    email_valid, email_error = validate_email(email)
    if not email_valid:
        errors.append(email_error)
    
    # パスワードバリデーション
    password_valid, password_error = validate_password(password)
    if not password_valid:
        errors.append(password_error)
    
    # 名前バリデーション
    name_valid, name_error = validate_name(name)
    if not name_valid:
        errors.append(name_error)
    
    return len(errors) == 0, errors

def validate_login_input(email: str, password: str) -> Tuple[bool, List[str]]:
    """
    ログイン入力のバリデーション（より緩い制約）
    
    Returns:
        Tuple[bool, List[str]]: (すべて有効かどうか, エラーメッセージのリスト)
    """
    errors = []
    
    # ログイン時は基本的なチェックのみ
    if not email:
        errors.append("メールアドレスを入力してください")
    elif not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        errors.append("正しいメールアドレスの形式で入力してください")
    
    if not password:
        errors.append("パスワードを入力してください")
    elif len(password) < 1:
        errors.append("パスワードを入力してください")
    
    return len(errors) == 0, errors 