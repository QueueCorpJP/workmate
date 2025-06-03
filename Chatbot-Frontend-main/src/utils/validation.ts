/**
 * フロントエンド用バリデーション関数
 */

export interface ValidationResult {
  isValid: boolean;
  message: string;
}

export const validateEmail = (email: string): ValidationResult => {
  if (!email) {
    return { isValid: false, message: "メールアドレスは必須です" };
  }

  if (email.length < 5) {
    return { isValid: false, message: "メールアドレスは5文字以上で入力してください" };
  }

  if (email.length > 100) {
    return { isValid: false, message: "メールアドレスは100文字以下で入力してください" };
  }

  const emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
  if (!emailPattern.test(email)) {
    return { isValid: false, message: "正しいメールアドレスの形式で入力してください" };
  }

  const forbiddenChars = ['<', '>', '"', "'", '\\', '/', '%', '&'];
  if (forbiddenChars.some(char => email.includes(char))) {
    return { isValid: false, message: "メールアドレスに使用できない文字が含まれています" };
  }

  if (email.includes('..')) {
    return { isValid: false, message: "連続するドット(..)は使用できません" };
  }

  if ((email.match(/@/g) || []).length !== 1) {
    return { isValid: false, message: "@マークは1つだけ含める必要があります" };
  }

  return { isValid: true, message: "" };
};

export const validatePassword = (password: string): ValidationResult => {
  if (!password) {
    return { isValid: false, message: "パスワードは必須です" };
  }

  if (password.length < 8) {
    return { isValid: false, message: "パスワードは8文字以上で入力してください" };
  }

  if (password.length > 50) {
    return { isValid: false, message: "パスワードは50文字以下で入力してください" };
  }

  if (!/[a-zA-Z]/.test(password)) {
    return { isValid: false, message: "英字を含める必要があります" };
  }

  if (!/[0-9]/.test(password)) {
    return { isValid: false, message: "数字を含める必要があります" };
  }

  if (!/[a-z]/.test(password)) {
    return { isValid: false, message: "小文字を含める必要があります" };
  }

  if (!/[A-Z]/.test(password)) {
    return { isValid: false, message: "大文字を含める必要があります" };
  }

  const commonPasswords = [
    'password', 'password123', '12345678', 'qwerty', 'abc123',
    'admin', 'admin123', 'user123', 'test123', '11111111',
    'password1', '123456789', 'welcome', 'letmein', 'monkey'
  ];

  if (commonPasswords.includes(password.toLowerCase())) {
    return { isValid: false, message: "一般的すぎるパスワードです。より複雑なものを設定してください" };
  }

  // 連続する同じ文字のチェック
  for (let i = 0; i < password.length - 2; i++) {
    if (password[i] === password[i+1] && password[i+1] === password[i+2]) {
      return { isValid: false, message: "同じ文字を3文字以上連続して使用できません" };
    }
  }

  // 連続する数字のチェック
  const consecutivePatterns = ['012', '123', '234', '345', '456', '567', '678', '789', '987', '876', '765', '654', '543', '432', '321', '210'];
  for (const pattern of consecutivePatterns) {
    if (password.toLowerCase().includes(pattern)) {
      return { isValid: false, message: "連続する数字や文字は避けてください" };
    }
  }

  return { isValid: true, message: "" };
};

export const validateName = (name: string): ValidationResult => {
  if (!name) {
    return { isValid: false, message: "名前は必須です" };
  }

  if (name.trim().length < 1) {
    return { isValid: false, message: "名前を入力してください" };
  }

  if (name.length > 50) {
    return { isValid: false, message: "名前は50文字以下で入力してください" };
  }

  if (name.trim() === "") {
    return { isValid: false, message: "名前に空白のみは使用できません" };
  }

  const forbiddenChars = ['<', '>', '"', "'", '\\', '/', '%', '&', '|', '*', '?', ':'];
  if (forbiddenChars.some(char => name.includes(char))) {
    return { isValid: false, message: "名前に使用できない文字が含まれています" };
  }

  return { isValid: true, message: "" };
};

export const getPasswordStrength = (password: string): { strength: number; label: string; color: string } => {
  let score = 0;
  
  if (password.length >= 8) score += 1;
  if (password.length >= 12) score += 1;
  if (/[a-z]/.test(password)) score += 1;
  if (/[A-Z]/.test(password)) score += 1;
  if (/[0-9]/.test(password)) score += 1;
  if (/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)) score += 1;
  
  if (score <= 2) {
    return { strength: score, label: "弱い", color: "#f44336" };
  } else if (score <= 4) {
    return { strength: score, label: "普通", color: "#ff9800" };
  } else {
    return { strength: score, label: "強い", color: "#4caf50" };
  }
}; 