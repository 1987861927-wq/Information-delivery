import SwiftUI

struct ArticleRowView: View {
    let article: Article

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(article.source)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                if article.isPreprint {
                    Text("预印本")
                        .font(.caption2)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(.orange.opacity(0.15))
                        .clipShape(Capsule())
                }
            }

            Text(article.chineseTitle ?? article.title)
                .font(.headline)
                .lineLimit(2)

            if let summary = article.summary {
                Text(summary)
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                    .lineLimit(3)
            }
        }
        .padding(.vertical, 6)
    }
}
