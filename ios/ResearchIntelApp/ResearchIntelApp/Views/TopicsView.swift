import SwiftUI

struct TopicsView: View {
    @State private var topics: [Topic] = []
    @State private var selected: Set<String> = ["neuroscience", "biomaterials", "ai", "orthopedics"]

    var body: some View {
        NavigationStack {
            List(topics) { topic in
                Toggle(isOn: Binding(
                    get: { selected.contains(topic.slug) },
                    set: { isOn in
                        if isOn {
                            selected.insert(topic.slug)
                        } else {
                            selected.remove(topic.slug)
                        }
                    }
                )) {
                    VStack(alignment: .leading, spacing: 4) {
                        Text(topic.name)
                            .font(.headline)
                        Text(topic.description)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }
            }
            .navigationTitle("主题")
            .task {
                do {
                    topics = try await APIClient.shared.fetchTopics()
                } catch {
                    topics = []
                }
            }
        }
    }
}
