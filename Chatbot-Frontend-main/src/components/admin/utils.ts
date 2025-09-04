/**
 * Format a date string as-is without timezone conversion
 * @param dateString - The date string to format
 * @returns Formatted date string without timezone conversion
 */
export const formatDate = (dateString: string): string => {
  if (!dateString) return '情報なし';

  const date = new Date(dateString);
  // タイムゾーン変換なしで、そのままの時刻を表示
  return new Intl.DateTimeFormat('ja-JP', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
    // timeZone指定を削除してそのまま表示
  }).format(date);
};

/**
 * Format a date string to JST (for cases where JST conversion is explicitly needed)
 * @param dateString - The date string to format (assumed to be UTC)
 * @returns Formatted date string in Japan time
 */
export const formatDateJST = (dateString: string): string => {
  if (!dateString) return '情報なし';

  const date = new Date(dateString);
  return new Intl.DateTimeFormat('ja-JP', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    timeZone: 'Asia/Tokyo'
  }).format(date);
};

/**
 * Format a date string to Japanese date format (YYYY/MM/DD) without timezone conversion
 * @param dateString - The date string to format
 * @returns Formatted date string (date only)
 */
export const formatDateOnly = (dateString: string): string => {
  if (!dateString) return '情報なし';

  const date = new Date(dateString);
  return new Intl.DateTimeFormat('ja-JP', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
    // timeZone指定を削除してそのまま表示
  }).format(date);
};

/**
 * Format a date string to Japanese datetime format with custom options without timezone conversion
 * @param dateString - The date string to format
 * @param options - Additional formatting options
 * @returns Formatted date string without timezone conversion
 */
export const formatDateCustom = (
  dateString: string, 
  options: Intl.DateTimeFormatOptions = {}
): string => {
  if (!dateString) return '情報なし';

  const date = new Date(dateString);
  return new Intl.DateTimeFormat('ja-JP', {
    // timeZone指定を削除してそのまま表示
    ...options
  }).format(date);
};

/**
 * Generate chart data for category distribution with enhanced styling
 * @param categories - Object with category names as keys and counts as values
 * @param colors - Array of color strings
 * @returns Chart.js data object
 */
export const getCategoryChartData = (
  categories: Record<string, number> | Array<{category: string, count: number}>,
  colors: string[]
) => {
  // Convert array format to record format if needed
  const categoriesRecord = Array.isArray(categories)
    ? categories.reduce((acc, item) => {
        acc[item.category] = item.count;
        return acc;
      }, {} as Record<string, number>)
    : categories;

  const labels = Object.keys(categoriesRecord);
  const data = Object.values(categoriesRecord);

  // Professional business color palette
  const professionalColors = [
    '#3b82f6',  // Blue - Primary business color
    '#10b981',  // Emerald - Success/Growth
    '#f59e0b',  // Amber - Warning/Attention
    '#ef4444',  // Red - Issues/Urgent
    '#8b5cf6',  // Violet - Innovation
    '#06b6d4',  // Cyan - Information
    '#84cc16',  // Lime - Positive trends
    '#f97316',  // Orange - Medium priority
    '#ec4899',  // Pink - Special categories
    '#6b7280'   // Gray - Neutral/Other
  ];

  // Solid colors for borders and hover states
  const solidColors = [
    '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
    '#06b6d4', '#84cc16', '#f97316', '#ec4899', '#6b7280'
  ];

  const borderColors = solidColors.map(color => color + 'CC'); // Add transparency
  const hoverColors = solidColors.map(color => color + 'EE'); // Lighter transparency

  return {
    labels,
    datasets: [
      {
        label: 'カテゴリ分布',
        data,
        backgroundColor: professionalColors.slice(0, labels.length),
        borderColor: '#ffffff',
        borderWidth: 2,
        hoverBackgroundColor: hoverColors.slice(0, labels.length),
        hoverBorderColor: '#ffffff',
        hoverBorderWidth: 3,
        borderRadius: 8,
        borderSkipped: false,
        // Chart.js 3.x doesn't support shadow directly
        // Instead, we'll use the updated styling in the component
      }
    ]
  };
};

/**
 * Generate chart data for sentiment distribution with neutral consolidation
 * @param sentiments - Object with sentiment names as keys and counts as values
 * @param colors - Object with sentiment names as keys and color strings as values
 * @returns Chart.js data object
 */
export const getSentimentChartData = (
  sentiments: Record<string, number> | Array<{sentiment: string, count: number}>,
  colors: Record<string, string>
) => {
  // Convert array format to record format if needed
  const sentimentsRecord = Array.isArray(sentiments)
    ? sentiments.reduce((acc, item) => {
        acc[item.sentiment] = item.count;
        return acc;
      }, {} as Record<string, number>)
    : sentiments;

  // Consolidate neutral sentiments (combine english and japanese variants)
  const consolidatedSentiments: Record<string, number> = {};
  let neutralCount = 0;

  Object.entries(sentimentsRecord).forEach(([sentiment, count]) => {
    const lowerSentiment = sentiment.toLowerCase();
    if (lowerSentiment === 'neutral' || lowerSentiment === 'ニュートラル' || sentiment === '中立') {
      neutralCount += count;
    } else if (lowerSentiment === 'positive' || lowerSentiment === 'ポジティブ' || sentiment === '肯定的') {
      consolidatedSentiments['ポジティブ'] = (consolidatedSentiments['ポジティブ'] || 0) + count;
    } else if (lowerSentiment === 'negative' || lowerSentiment === 'ネガティブ' || sentiment === '否定的') {
      consolidatedSentiments['ネガティブ'] = (consolidatedSentiments['ネガティブ'] || 0) + count;
    } else {
      consolidatedSentiments[sentiment] = count;
    }
  });

  if (neutralCount > 0) {
    consolidatedSentiments['ニュートラル'] = neutralCount;
  }

  const labels = Object.keys(consolidatedSentiments);
  const data = Object.values(consolidatedSentiments);

  // Professional business colors for sentiment analysis
  const professionalSentimentColors: Record<string, string> = {
    'ポジティブ': '#10b981',   // Emerald - Positive sentiment
    'ネガティブ': '#ef4444',   // Red - Negative sentiment
    'ニュートラル': '#6b7280', // Gray - Neutral sentiment
    'positive': '#10b981',
    'negative': '#ef4444',
    'neutral': '#6b7280'
  };

  // Lighter colors for hover states
  const hoverSentimentColors: Record<string, string> = {
    'ポジティブ': '#34d399',   // Lighter emerald
    'ネガティブ': '#f87171',   // Lighter red
    'ニュートラル': '#9ca3af', // Lighter gray
    'positive': '#34d399',
    'negative': '#f87171',
    'neutral': '#9ca3af'
  };

  return {
    labels,
    datasets: [
      {
        label: '感情分布',
        data,
        backgroundColor: labels.map(label => 
          professionalSentimentColors[label] || colors[label] || '#6b7280'
        ),
        borderColor: '#ffffff',
        borderWidth: 4,
        hoverBackgroundColor: labels.map(label => 
          hoverSentimentColors[label] || colors[label] || '#9ca3af'
        ),
        hoverBorderColor: '#ffffff',
        hoverBorderWidth: 6,
        // Chart.js 3.x styling handled in component
      }
    ]
  };
};

/**
 * Convert analysis data to CSV format and trigger download
 * @param analysis - Analysis result data
 */
export const exportAnalysisToCSV = (analysis: any) => {
  try {
    // 今日の日付を取得
    const today = new Date();
    const dateStr = today.toISOString().split('T')[0];

    // CSVコンテンツの作成
    let csvContent = "データタイプ,項目,値,割合\n";

    // カテゴリ分布
    let categoryDistribution: Record<string, number>;
    
    if (Array.isArray(analysis.category_distribution)) {
      categoryDistribution = analysis.category_distribution.reduce((acc: Record<string, number>, item: {category: string, count: number}) => {
        acc[item.category] = item.count;
        return acc;
      }, {} as Record<string, number>);
    } else {
      categoryDistribution = analysis.category_distribution;
    }
    
    const categoryValues = Object.values(categoryDistribution) as number[];
    const categoryTotal = categoryValues.reduce((a, b) => a + b, 0);
    
    Object.entries(categoryDistribution).forEach(([category, count]) => {
      const percentage = ((count as number / categoryTotal) * 100).toFixed(2);
      csvContent += `カテゴリ分布,${category},${count},${percentage}%\n`;
    });

    // 感情分布
    let sentimentDistribution: Record<string, number>;
    
    if (Array.isArray(analysis.sentiment_distribution)) {
      sentimentDistribution = analysis.sentiment_distribution.reduce((acc: Record<string, number>, item: {sentiment: string, count: number}) => {
        acc[item.sentiment] = item.count;
        return acc;
      }, {} as Record<string, number>);
    } else {
      sentimentDistribution = analysis.sentiment_distribution;
    }
    
    const sentimentValues = Object.values(sentimentDistribution) as number[];
    const sentimentTotal = sentimentValues.reduce((a, b) => a + b, 0);
    
    Object.entries(sentimentDistribution).forEach(([sentiment, count]) => {
      const percentage = ((count as number / sentimentTotal) * 100).toFixed(2);
      csvContent += `感情分布,${sentiment},${count},${percentage}%\n`;
    });

    // よくある質問
    if (analysis.common_questions && Array.isArray(analysis.common_questions)) {
      analysis.common_questions.forEach((item: any) => {
        if (typeof item === 'string') {
          csvContent += `よくある質問,${item},1\n`;
        } else if (item.question) {
          csvContent += `よくある質問,${item.question},${item.count || 1}\n`;
        }
      });
    }

    // AI洞察
    csvContent += `\nAI洞察\n${analysis.insights.replace(/\n/g, " ")}\n`;

    // 詳細ビジネス分析（存在する場合）
    if (analysis.business_analysis_completed) {
      csvContent += "\n詳細ビジネス分析\n";
      if (analysis.detailed_topic_analysis) {
        csvContent += `\n1. 頻出トピック/質問とその傾向分析\n${analysis.detailed_topic_analysis.replace(/\n/g, " ")}\n`;
      }
      if (analysis.efficiency_opportunities) {
        csvContent += `\n2. 業務効率化の機会\n${analysis.efficiency_opportunities.replace(/\n/g, " ")}\n`;
      }
      if (analysis.frustration_points) {
        csvContent += `\n3. 社員のフラストレーションポイント\n${analysis.frustration_points.replace(/\n/g, " ")}\n`;
      }
      if (analysis.improvement_suggestions) {
        csvContent += `\n4. 製品/サービス改善の示唆\n${analysis.improvement_suggestions.replace(/\n/g, " ")}\n`;
      }
      if (analysis.communication_gaps) {
        csvContent += `\n5. コミュニケーションギャップ\n${analysis.communication_gaps.replace(/\n/g, " ")}\n`;
      }
      if (analysis.specific_recommendations) {
        csvContent += `\n具体的な改善提案\n${analysis.specific_recommendations.replace(/\n/g, " ")}\n`;
      }
    }

    // CSVファイルのダウンロード
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `チャット分析_${dateStr}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  } catch (error) {
    console.error('CSV出力エラー:', error);
    alert('CSV出力中にエラーが発生しました。');
  }
};

/**
 * 
 * @param url 
 * @returns boolean
 */
export const isValidURL = (url: string): boolean =>
  /^(https?:\/\/)?[\w.-]+\.[a-z]{2,}(\S*)$/i.test(url);