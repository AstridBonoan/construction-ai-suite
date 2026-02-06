import React from 'react';
import {
  Box,
  Container,
  Heading,
  VStack,
  SimpleGrid,
  Card,
  CardBody,
  Text,
  HStack,
  Progress,
  useColorModeValue,
} from '@chakra-ui/react';

const Insights = () => {
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');
  const chartBg = useColorModeValue('gray.100', 'gray.700');

  return (
    <Container maxW="5xl" py={8}>
      <VStack spacing={8} align="stretch">
        <Box>
          <Heading size="lg" mb={2}>Insights & Analysis</Heading>
          <Text color="gray.600">
            Real-time risk scores, delay propagation, and dependency analysis.
          </Text>
        </Box>
        <SimpleGrid columns={{ base: 1, md: 2 }} spacing={6}>
          <Card bg={bgColor} border="1px" borderColor={borderColor}>
            <CardBody>
              <VStack align="start" spacing={4}>
                <Heading size="sm">Risk Score Distribution</Heading>
                <Box w="full" h="200px" bg={chartBg} borderRadius="md" display="flex" alignItems="center" justifyContent="center" color="gray.500">
                  Chart Placeholder
                </Box>
              </VStack>
            </CardBody>
          </Card>
          <Card bg={bgColor} border="1px" borderColor={borderColor}>
            <CardBody>
              <VStack align="start" spacing={4}>
                <Heading size="sm">Delay Dependencies</Heading>
                <Box w="full" h="200px" bg={chartBg} borderRadius="md" display="flex" alignItems="center" justifyContent="center" color="gray.500">
                  Timeline Graph
                </Box>
              </VStack>
            </CardBody>
          </Card>
        </SimpleGrid>
        <Card bg={bgColor} border="1px" borderColor={borderColor}>
          <CardBody>
            <VStack align="start" spacing={4}>
              <Heading size="sm">Project Health Status</Heading>
              <VStack w="full" spacing={3}>
                <HStack w="full" justify="space-between">
                  <Text fontSize="sm" fontWeight="medium">Foundation Phase</Text>
                  <Progress value={72} size="sm" w="40%" colorScheme="orange" />
                </HStack>
                <HStack w="full" justify="space-between">
                  <Text fontSize="sm" fontWeight="medium">Framing</Text>
                  <Progress value={45} size="sm" w="40%" colorScheme="red" />
                </HStack>
                <HStack w="full" justify="space-between">
                  <Text fontSize="sm" fontWeight="medium">MEP Systems</Text>
                  <Progress value={30} size="sm" w="40%" colorScheme="red" />
                </HStack>
              </VStack>
            </VStack>
          </CardBody>
        </Card>
      </VStack>
    </Container>
  );
};

export default Insights;
