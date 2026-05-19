import SwiftUI

struct ArticleDetailView: View {
    let article: Article

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                Text(article.chineseTitle ?? article.title)
                    .font(.title2.bold())

                Text(article.source)
                    .font(.subheadline)
                    .foregroundStyle(.secondary)

                if let summary = article.summary {
                    SectionBlock(title: "中文精炼", text: summary)
                }

                if let abstract = article.abstract {
                    SectionBlock(title: "原始摘要", text: abstract)
                }

                if let url = URL(string: article.url) {
                    Link("打开原文", destination: url)
                        .buttonStyle(.borderedProminent)
                }
            }
            .padding()
        }
        .navigationTitle("详情")
        .navigationBarTitleDisplayMode(.inline)
    }
}

private struct SectionBlock: View {
    let title: String
    let text: String

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(title)
                .font(.headline)
            Text(text)
                .font(.body)
        }
    }
}
